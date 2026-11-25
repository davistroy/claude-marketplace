import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

import pytest

TEMPLATE = (
    Path(__file__).resolve().parents[3] / "skills" / "document-repo" / "templates" / "explorer"
)
OWN_FILES = ["index.html", "app.js", "styles.css"]


def test_template_files_exist() -> None:
    for name in [*OWN_FILES, "vendor/mermaid.min.js", "vendor/README.md"]:
        assert (TEMPLATE / name).is_file(), name
    assert not (TEMPLATE / "data").exists(), "the template must not ship data/"


def test_index_loads_only_local_scripts_in_order() -> None:
    html = (TEMPLATE / "index.html").read_text()
    assert re.findall(r'<script src="([^"]+)"', html) == [
        "data/model.js",
        "vendor/mermaid.min.js",
        "app.js",
    ]
    assert re.findall(r'<link rel="stylesheet" href="([^"]+)"', html) == ["styles.css"]


def test_no_network_in_own_files() -> None:
    for name in OWN_FILES:
        text = (TEMPLATE / name).read_text()
        assert "http://" not in text and "https://" not in text, name
        for banned in ("fetch(", "XMLHttpRequest", "import(", "@import", "sendBeacon", "WebSocket"):
            assert banned not in text, f"{name} uses {banned}"


def test_mermaid_checksum_matches_readme() -> None:
    readme = (TEMPLATE / "vendor" / "README.md").read_text()
    match = re.search(r"sha256: ([0-9a-f]{64})", readme)
    assert match, "vendor/README.md must record the sha256"
    digest = hashlib.sha256((TEMPLATE / "vendor" / "mermaid.min.js").read_bytes()).hexdigest()
    assert digest == match.group(1)
    assert "mermaid@11.17.2" in readme


CSP_DIRECTIVES = [
    "default-src 'none'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    "base-uri 'none'",
    "form-action 'none'",
]


def test_index_sets_the_content_security_policy() -> None:
    html = (TEMPLATE / "index.html").read_text()
    metas = re.findall(
        r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">', html, flags=re.I
    )
    assert len(metas) == 1, metas
    assert [d.strip() for d in metas[0].split(";")] == CSP_DIRECTIVES
    # The policy only governs what loads after it, so it must precede every script and stylesheet.
    assert html.index("Content-Security-Policy") < html.index("<link")
    assert html.index("Content-Security-Policy") < html.index("<script")


# Runs the real app.js under node against a stub DOM. It renders each hash in turn (the first on
# start-up, the rest through the hashchange listener) and prints, per hash, what landed in <main>,
# the search box value and the id that was scrolled into view. The stub only has to be good enough
# for app.js to start: this checks the strings the app builds (links, escaping), not layout or
# Mermaid, which the browser checks cover.
RENDER = r"""
const fs = require('fs');
const vm = require('vm');
const appPath = process.argv[1];
const { model, hashes, lens } = JSON.parse(fs.readFileSync(0, 'utf8'));
const els = {};
const listeners = {};
let scrolled = null;
const el = (id) => els[id] || (els[id] = {
  id, innerHTML: '', textContent: '', value: '', dataset: {}, classList: { toggle() {} },
  setAttribute() {}, addEventListener() {}, querySelectorAll: () => [],
  scrollIntoView() { scrolled = id; },
});
globalThis.window = {
  PROJECT_MODEL: model,
  localStorage: { getItem: (k) => (k === 'document-repo-lens' ? lens : null), setItem() {} },
  addEventListener(type, fn) { listeners[type] = fn; }, scrollTo() {}, setTimeout() {},
  clearTimeout() {},
};
globalThis.document = { getElementById: el, querySelectorAll: () => [], activeElement: null };
globalThis.location = { hash: hashes[0] };
vm.runInThisContext(fs.readFileSync(appPath, 'utf8'));
const out = [];
hashes.forEach((hash, i) => {
  if (i) { scrolled = null; location.hash = hash; listeners.hashchange(); }
  out.push({ hash, html: String(els.view.innerHTML), search: els.search.value, scrolled });
});
process.stdout.write(JSON.stringify(out));
"""
SAMPLE_MODEL = Path(__file__).parent / "fixtures" / "sample_model.json"
SOURCE_URL = "https://github.com/example/demo"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
LENSES = ["functional", "technical"]


def sample_model() -> dict:
    return json.loads(SAMPLE_MODEL.read_text())


def render_many(model: dict, hashes: list[str], lens: str = "functional") -> list[dict]:
    """Render each hash in one explorer session for ``model`` and return what each one showed."""
    node = shutil.which("node")
    if node is None:
        message = "node is not available; the explorer app cannot be run"
        if os.environ.get("CI"):
            pytest.fail(message)
        pytest.skip(message)
    proc = subprocess.run(
        [node, "-e", RENDER, str(TEMPLATE / "app.js")],
        input=json.dumps({"model": model, "hashes": hashes, "lens": lens}),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def render(hash_route: str, edit=None) -> str:
    """Render one route of the explorer for the fixture model, optionally edited first."""
    model = sample_model()
    if edit:
        edit(model)
    return render_many(model, [hash_route])[0]["html"]


def test_file_links_use_the_repo_url() -> None:
    out = render("#/modules/src-api")
    assert f'href="{SOURCE_URL}/blob/{COMMIT}/src/api/routes.py#L12"' in out
    assert 'rel="noopener noreferrer"' in out


@pytest.mark.parametrize(
    "repo_url",
    [
        None,
        "",
        "javascript:alert(1)",
        "JaVaScRiPt:alert(1)",
        " javascript:alert(1)",
        "\tjavascript:alert(1)",
        " https://github.com/example/demo",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
        "ftp://example.com/repo",
        "//evil.example/repo",
        "github.com/example/demo",
        42,
    ],
)
def test_file_links_are_plain_text_unless_repo_url_is_http(repo_url) -> None:
    def edit(model) -> None:
        model["meta"]["repo_url"] = repo_url

    out = render("#/modules/src-api", edit)
    hrefs = re.findall(r'href="([^"]*)"', out)
    assert hrefs and all(h.startswith("#/") for h in hrefs), hrefs
    assert '<a class="file"' not in out
    assert '<code class="file">src/api/routes.py:12</code>' in out


def test_model_strings_are_escaped() -> None:
    payload = "<img src=x onerror=alert(1)>"

    def edit(model) -> None:
        model["modules"][1]["name"] = payload
        model["modules"][1]["invariants"] = [payload]

    out = render("#/modules/src-api", edit)
    assert "<img" not in out
    assert "&lt;img src=x onerror=alert(1)&gt;" in out


# ---- hostile model -------------------------------------------------------------------------------
# Every model string is written by an AI agent from an untrusted repo. The test below replaces every
# free-text field with a payload that tries a raw tag, an attribute breakout and a script URL, then
# renders every route in both lenses and parses the result as HTML.

# Strings that are identifiers or enum values: changing them would break cross-references (so less
# of the page would render) without testing anything new. Ids get their own hostile-route test.
ID_KEYS = {"id", "module_ids", "internal", "from", "to", "ref_id", "ref_type", "kind", "status"}
META_KEEP = {"schema_version", "generated_at", "source_commit", "repo_name"}
# A web URL passes the app's http(s) check, so a quote in it reaches an href attribute. Only esc()
# stops it breaking out of the attribute.
HOSTILE_REPO_URL = 'https://example.com/r"onmouseover="alert(1)"x=\''
LOCAL_HREF = re.compile(r"^(#/|\.\./)")


def payload(tag: str) -> str:
    return f"\"'><img src=x onerror={tag}>`<svg onload={tag}>`<script>{tag}</script>"


def hostile_model() -> tuple[dict, list[str]]:
    """The fixture with every free-text string replaced by a payload naming its field."""
    model = sample_model()
    markers: list[str] = []

    def mark() -> str:
        markers.append(f"xss{len(markers)}")
        return payload(markers[-1])

    # Glossary terms are both text and cross-references: rename them and every reference together.
    renamed = {g["term"]: mark() for g in model["glossary"]}
    for g in model["glossary"]:
        g["term"] = renamed[g["term"]]
    for p in model["paths"]:
        for s in p["steps"]:
            if s["ref_type"] == "glossary":
                s["ref_id"] = renamed[s["ref_id"]]
            elif s["ref_type"] == "doc":
                s["ref_id"] = mark()

    def walk(node):
        if isinstance(node, list):
            return [mark() if isinstance(x, str) else walk(x) for x in node]
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ID_KEYS or (key == "term" and value in renamed.values()):
                    continue
                node[key] = mark() if isinstance(value, str) else walk(value)
        return node

    meta = model.pop("meta")
    walk(model)
    model["meta"] = {k: meta[k] for k in META_KEEP} | {"repo_url": HOSTILE_REPO_URL}
    # Line numbers are integers in a valid model, but the app must not trust that either.
    for f in model["flows"]:
        for s in f["steps"]:
            s["line_start"], s["line_end"] = "1", "z" + mark()
    for m in model["modules"]:
        for i in m["interface"]:
            i["line"] = mark()
    return model, markers


def every_route(model: dict) -> list[str]:
    q = urllib.parse.quote
    evil = payload("route")
    routes = ["#/overview", "#/architecture", "#/modules", "#/tours", "#/glossary", "#/paths"]
    routes += [f"#/modules/{q(m['id'])}" for m in model["modules"]]
    routes += [f"#/tours/{q(f['id'])}" for f in model["flows"]]
    routes += [f"#/paths/{q(p['id'])}" for p in model["paths"]]
    routes += [f"#/glossary/{q(g['term'], safe='')}" for g in model["glossary"]]
    routes += [f"#/search/{q(t, safe='')}" for t in ("img", "onerror", "xss", evil)]
    routes += [f"#/{kind}/{q(evil, safe='')}" for kind in ("modules", "tours", "paths", "glossary")]
    routes += [f"#/{q(evil, safe='')}", *HOSTILE_ROUTES]
    return routes


class Audit(HTMLParser):
    """Collects what an HTML string would really create: elements, attributes and text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.handlers: list[str] = []
        self.urls: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs) -> None:
        self.tags.append(tag)
        for name, value in attrs:
            if name.startswith("on"):
                self.handlers.append(f"<{tag} {name}>")
            if name in {"href", "src", "action", "formaction", "xlink:href", "srcdoc"}:
                self.urls.append(value or "")
            self.text.append(value or "")

    def handle_data(self, data) -> None:
        self.text.append(data)


def audit(html: str) -> Audit:
    parser = Audit()
    parser.feed(html)
    parser.close()
    return parser


@pytest.mark.parametrize("lens", LENSES)
def test_hostile_model_strings_never_become_markup(lens) -> None:
    model, markers = hostile_model()
    routes = every_route(model)
    seen = ""
    for page in render_many(model, routes, lens):
        found = audit(page["html"])
        where = f"{page['hash']} ({lens})"
        assert not {"img", "svg", "script", "iframe", "object", "embed"} & set(found.tags), where
        assert not found.handlers, (where, found.handlers)
        for url in found.urls:
            blob = url.startswith(HOSTILE_REPO_URL + "/blob/")
            assert LOCAL_HREF.match(url) or blob, (where, url)
        seen += "\n".join(found.text)
    # The payloads did reach the page, as text: the test is not passing on an empty render.
    missing = [m for m in markers if f"onerror={m}>" not in seen]
    assert len(missing) <= len(markers) // 4, f"{len(missing)}/{len(markers)} payloads never shown"


HOSTILE_ROUTES = [
    "#/constructor/" + urllib.parse.quote("<img src=x onerror=alert(1)>", safe=""),
    "#/__proto__",
    "#/toString",
    "#/hasOwnProperty/x",
    "#/valueOf",
    "#/constructor",
]


def test_prototype_route_names_fall_back_to_the_overview() -> None:
    pages = render_many(sample_model(), ["#/overview", *HOSTILE_ROUTES])
    overview = pages[0]["html"]
    assert "<h1>Demo</h1>" in overview
    for page in pages[1:]:
        assert page["html"] == overview, page["hash"]


def test_glossary_anchors_are_unique_and_scroll_to_their_own_term() -> None:
    terms = ["C++", "C#", "C", "中文", "日本語", "a/b", "a-b", "a b", "x%2Fy", "?", "#", "it's"]
    model = sample_model()
    model["glossary"] = [
        {"term": t, "definition": f"def {i}", "kind": "domain", "module_ids": []}
        for i, t in enumerate(terms)
    ]
    model["paths"] = [
        {**p, "steps": [s for s in p["steps"] if s["ref_type"] != "glossary"]}
        for p in model["paths"]
    ]
    hashes = ["#/glossary"] + [f"#/glossary/{urllib.parse.quote(t, safe='')}" for t in terms]
    pages = render_many(model, hashes)
    ids = re.findall(r'<dt id="([^"]+)"', pages[0]["html"])
    assert len(ids) == len(terms) and len(set(ids)) == len(ids), ids
    for term, page in zip(terms, pages[1:]):
        hit = re.search(r'<dt id="([^"]+)" class="hit">([^<]*)</dt>', page["html"])
        assert hit, term
        assert html.unescape(hit.group(2)) == term
        assert page["scrolled"] == hit.group(1), (term, page["scrolled"])


def test_direct_search_load_fills_the_search_box() -> None:
    pages = render_many(sample_model(), ["#/search/foo%20bar", "#/overview"])
    assert pages[0]["search"] == "foo bar"
    assert pages[1]["search"] == ""


def test_search_reports_truncation() -> None:
    model = sample_model()
    model["glossary"] += [
        {"term": f"zz term {i}", "definition": "x", "kind": "tech", "module_ids": []}
        for i in range(150)
    ]
    out = render_many(model, ["#/search/zz"])[0]["html"]
    assert "150 results" in out and "showing 100 of 150" in out
    assert out.count("<li>") == 100
    few = render_many(sample_model(), ["#/search/note"])[0]["html"]
    assert "showing" not in few


def test_empty_glossary_says_none() -> None:
    model = sample_model()
    model["glossary"] = []
    model["paths"] = [
        {**p, "steps": [s for s in p["steps"] if s["ref_type"] != "glossary"]}
        for p in model["paths"]
    ]
    out = render_many(model, ["#/glossary"])[0]["html"]
    assert out == '<h1>Glossary</h1><p class="muted">None.</p>'
