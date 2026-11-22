import hashlib
import json
import os
import re
import shutil
import subprocess
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
    assert "mermaid@11.4.1" in readme


# Runs the real app.js under node against a stub DOM and prints what it rendered into <main>. The
# stub only has to be good enough for app.js to start: the page is not a browser, so this checks
# the strings the app builds (links, escaping), not layout or Mermaid.
RENDER = r"""
const fs = require('fs');
const vm = require('vm');
const [appPath, hash] = process.argv.slice(1);
const model = JSON.parse(fs.readFileSync(0, 'utf8'));
const els = {};
const el = (id) => els[id] || (els[id] = {
  id, innerHTML: '', textContent: '', value: '', dataset: {}, classList: { toggle() {} },
  setAttribute() {}, addEventListener() {}, querySelectorAll: () => [],
});
globalThis.window = {
  PROJECT_MODEL: model, localStorage: { getItem: () => null, setItem() {} },
  addEventListener() {}, scrollTo() {}, setTimeout() {}, clearTimeout() {},
};
globalThis.document = { getElementById: el, querySelectorAll: () => [], activeElement: null };
globalThis.location = { hash };
vm.runInThisContext(fs.readFileSync(appPath, 'utf8'));
process.stdout.write(els.view.innerHTML);
"""
SAMPLE_MODEL = Path(__file__).parent / "fixtures" / "sample_model.json"
SOURCE_URL = "https://github.com/example/demo"
COMMIT = "0123456789abcdef0123456789abcdef01234567"


def render(hash_route: str, edit=None) -> str:
    """Render one route of the explorer for the fixture model, optionally edited first."""
    node = shutil.which("node")
    if node is None:
        message = "node is not available; the explorer app cannot be run"
        if os.environ.get("CI"):
            pytest.fail(message)
        pytest.skip(message)
    model = json.loads(SAMPLE_MODEL.read_text())
    if edit:
        edit(model)
    proc = subprocess.run(
        [node, "-e", RENDER, str(TEMPLATE / "app.js"), hash_route],
        input=json.dumps(model),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


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
