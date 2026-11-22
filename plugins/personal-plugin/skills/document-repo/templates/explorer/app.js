/* Project Explorer. Renders window.PROJECT_MODEL (explorer/data/model.js).
 * Fixed template shipped by the document-repo skill; only data/ is generated.
 * No network access: every asset is local and nothing is fetched. */
(() => {
  'use strict';

  const M = window.PROJECT_MODEL;
  const view = document.getElementById('view');
  if (!M) {
    view.innerHTML = '<p class="empty">No project model found. Run the document-repo skill to generate <code>explorer/data/model.js</code>.</p>';
    return;
  }

  // ---- small helpers -------------------------------------------------------
  const store = {
    get(key) { try { return window.localStorage.getItem(key); } catch (e) { return null; } },
    set(key, value) { try { window.localStorage.setItem(key, value); } catch (e) { /* storage blocked */ } },
  };
  const LENS_KEY = 'document-repo-lens';
  let lens = store.get(LENS_KEY) === 'technical' ? 'technical' : 'functional';

  const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ESC[c]);
  const rich = (s) => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>');
  const lensText = (o) => (o && typeof o === 'object' ? o[lens] || o.functional || '' : o || '');
  const byId = (items, id) => items.find((x) => x.id === id);
  const href = (...parts) => '#/' + parts.map((p) => encodeURIComponent(p)).join('/');
  const list = (items, fn) => (items.length ? '<ul>' + items.map((x) => '<li>' + fn(x) + '</li>').join('') + '</ul>' : '<p class="muted">None.</p>');
  // A glossary anchor is the term's position in M.glossary, so two terms that differ only in
  // punctuation or script (C++ and C#, 中文 and 日本語) never share an id. Unknown terms get none.
  const termAnchor = (term) => {
    const i = M.glossary.findIndex((g) => g.term === term);
    return i < 0 ? '' : 'term-' + i;
  };
  const tags = (items) => (items.length ? '<ul class="chips">' + items.map((x) => '<li>' + esc(x) + '</li>').join('') + '</ul>' : '');

  // A link is built only from a web URL. Anything else in repo_url (a javascript: or data: URL, a
  // relative path, text with leading whitespace) renders the path as plain text, never an href.
  const WEB_URL = /^https?:\/\//i;
  function fileLink(path, line) {
    const label = esc(path) + (line ? ':' + esc(line) : '');
    const base = M.meta.repo_url;
    if (typeof base !== 'string' || !WEB_URL.test(base)) return '<code class="file">' + label + '</code>';
    const url = base.replace(/\/+$/, '') + '/blob/' + encodeURIComponent(M.meta.source_commit) + '/' +
      String(path).split('/').map((p) => encodeURIComponent(p)).join('/') + (line ? '#L' + encodeURIComponent(line) : '');
    return '<a class="file" href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + label + '</a>';
  }
  const moduleLink = (id) => {
    const m = byId(M.modules, id);
    return '<a href="' + esc(href('modules', id)) + '">' + esc(m ? m.name : id) + '</a>';
  };
  const componentName = (id) => { const c = byId(M.architecture.components, id); return c ? c.name : id; };
  const notFound = (kind, id) => '<h1>Not found</h1><p>No ' + kind + ' called <code>' + esc(id) + '</code>. <a href="#/overview">Back to the overview</a>.</p>';
  const inModule = (m, file) => (m.path === '.' ? !file.includes('/') : file === m.path || file.startsWith(m.path + '/'));
  const codeBlock = (code) => {
    const pre = '<pre><code>' + esc(code) + '</code></pre>';
    return lens === 'technical' ? pre : '<details><summary>Show the code</summary>' + pre + '</details>';
  };

  // ---- views ---------------------------------------------------------------
  function overview() {
    const p = M.project;
    return `
      <section class="hero">
        <p class="eyebrow">${esc(M.meta.repo_name)}</p>
        <h1>${esc(p.name)}</h1>
        <p class="tagline">${rich(p.tagline)}</p>
        <p class="lead">${rich(lensText(p.purpose))}</p>
      </section>
      <h2>Who it is for</h2>${tags(p.users)}
      <h2>What it can do</h2>
      <div class="cards">${p.capabilities.map((c) => `<article class="card"><h3>${esc(c.title)}</h3><p>${rich(c[lens])}</p></article>`).join('')}</div>
      <h2>Built with</h2>
      <table><thead><tr><th>Technology</th><th>Role</th></tr></thead>
      <tbody>${p.tech_stack.map((t) => `<tr><td>${esc(t.name)}</td><td>${rich(t.role)}</td></tr>`).join('')}</tbody></table>
      <h2>Run it</h2>
      ${p.run.setup.length ? '<h3>Setup</h3><ol>' + p.run.setup.map((s) => `<li>${rich(s)}</li>`).join('') + '</ol>' : ''}
      ${p.run.commands.map((c) => `<p class="muted">${esc(c.label)}</p><pre><code>${esc(c.command)}</code></pre>`).join('')}
      <h2>Where to go next</h2>
      <div class="cards">${M.paths.map((pa) => `<a class="card link-card" href="${esc(href('paths', pa.id))}"><h3>${esc(pa.title)}</h3><p>${esc(pa.audience)}</p></a>`).join('')}</div>`;
  }

  function architecture() {
    const a = M.architecture;
    return `<h1>Architecture</h1><p class="lead">${rich(lensText(a.summary))}</p>
      ${a.diagrams.map((d) => `<figure class="diagram"><figcaption>${esc(d.title)}</figcaption><pre class="mermaid-src">${esc(d.mermaid)}</pre></figure>`).join('')}
      ${a.diagrams.length ? '<p class="muted">Click a box in a diagram to open its module.</p>' : ''}
      <h2>Components</h2>
      <div class="cards">${a.components.map((c) => `<article class="card" id="comp-${esc(c.id)}">
        <h3>${esc(c.name)} <span class="tag">${esc(c.kind)}</span></h3>
        <p>${rich(lensText(c.description))}</p><p>${c.module_ids.map(moduleLink).join(' · ')}</p></article>`).join('')}</div>
      <h2>Connections</h2>
      ${list(a.connections, (k) => `<strong>${esc(componentName(k.from))}</strong> → <strong>${esc(componentName(k.to))}</strong>: ${rich(k.label)}`)}`;
  }

  function modules(id) {
    if (!id) {
      return `<h1>Modules</h1><p class="lead">Each module is one area of the code with one job.</p>
        <div class="cards">${M.modules.map((m) => `<a class="card link-card" href="${esc(href('modules', m.id))}">
          <h3>${esc(m.name)}</h3><p class="path"><code>${esc(m.path)}</code></p><p>${rich(lensText(m.purpose))}</p>
          ${m.status === 'not_analyzed' ? '<span class="tag warn">not analyzed</span>' : ''}</a>`).join('')}</div>`;
    }
    const m = byId(M.modules, id);
    if (!m) return notFound('module', id);
    const flowsHere = M.flows.filter((f) => f.steps.some((s) => inModule(m, s.file)));
    const terms = M.glossary.filter((g) => g.module_ids.includes(m.id));
    const usedBy = M.modules.filter((o) => o.dependencies.internal.includes(m.id));
    const iface = m.interface.length
      ? `<table><thead><tr><th>Name</th><th>What it does</th><th>Where</th></tr></thead><tbody>${m.interface.map((i) => `<tr>
          <td><code>${esc(i.name)}</code> <span class="tag">${esc(i.kind)}</span>${lens === 'technical' ? `<pre><code>${esc(i.signature)}</code></pre>` : ''}</td>
          <td>${rich(i.description)}</td><td>${fileLink(i.file, i.line)}</td></tr>`).join('')}</tbody></table>`
      : '<p class="muted">No public interface.</p>';
    return `<p class="crumbs"><a href="${esc(href('modules'))}">Modules</a> / ${esc(m.name)}</p>
      <h1>${esc(m.name)} ${m.status === 'not_analyzed' ? '<span class="tag warn">not analyzed</span>' : ''}</h1>
      <p class="path"><code>${esc(m.path)}</code></p>
      <p class="lead">${rich(lensText(m.purpose))}</p>
      <h2>Public interface</h2>${iface}
      <h2>Rules that must stay true</h2>${list(m.invariants, rich)}
      <h2>Depends on</h2>${list(m.dependencies.internal, moduleLink)}${tags(m.dependencies.external)}
      <h2>Used by</h2>${list(usedBy, (o) => moduleLink(o.id))}
      <h2>Key files</h2>${list(m.key_files, (f) => `${fileLink(f.path)} — ${rich(f.role)}`)}
      <h2>Tours through this module</h2>${list(flowsHere, (f) => `<a href="${esc(href('tours', f.id))}">${esc(f.title)}</a>`)}
      <h2>Terms</h2>${list(terms, (g) => `<a href="${esc(href('glossary', g.term))}">${esc(g.term)}</a>`)}`;
  }

  function tours(id) {
    if (!id) {
      return `<h1>Tours</h1><p class="lead">Each tour follows one thing the system does, step by step, through the real code.</p>
        <div class="cards">${M.flows.map((f) => `<a class="card link-card" href="${esc(href('tours', f.id))}">
          <h3>${esc(f.title)}</h3><p>${rich(lensText(f.summary))}</p><p class="muted">${f.steps.length} steps</p></a>`).join('')}</div>`;
    }
    const f = byId(M.flows, id);
    if (!f) return notFound('tour', id);
    return `<p class="crumbs"><a href="${esc(href('tours'))}">Tours</a> / ${esc(f.title)}</p>
      <h1>${esc(f.title)}</h1><p class="lead">${rich(lensText(f.summary))}</p>
      <ol class="steps">${f.steps.map((s, i) => `<li class="step" id="step-${i + 1}">
        <div class="step-num">${i + 1}</div>
        <div class="step-body"><h3>${esc(s.title)}</h3><p>${rich(lensText(s.text))}</p>
          <p>${fileLink(s.file, s.line_start)}${s.line_end > s.line_start ? '–' + esc(s.line_end) : ''}</p>
          ${s.snippet ? codeBlock(s.snippet) : ''}</div></li>`).join('')}</ol>`;
  }

  function glossary(term) {
    if (!M.glossary.length) return '<h1>Glossary</h1><p class="muted">None.</p>';
    const groups = [['domain', 'Domain terms'], ['tech', 'Technical terms']];
    return '<h1>Glossary</h1>' + groups.map(([kind, title]) => {
      const items = M.glossary.filter((g) => g.kind === kind).sort((a, b) => a.term.localeCompare(b.term));
      if (!items.length) return '';
      return `<h2>${title}</h2><dl class="glossary">${items.map((g) => `
        <dt id="${esc(termAnchor(g.term))}"${term === g.term ? ' class="hit"' : ''}>${esc(g.term)}</dt>
        <dd>${rich(g.definition)}${g.module_ids.length ? ' <span class="muted">— ' + g.module_ids.map(moduleLink).join(', ') + '</span>' : ''}</dd>`).join('')}</dl>`;
    }).join('');
  }

  function stepTarget(s) {
    if (s.ref_type === 'module') { const m = byId(M.modules, s.ref_id); return [href('modules', s.ref_id), m ? m.name : s.ref_id]; }
    if (s.ref_type === 'flow') { const f = byId(M.flows, s.ref_id); return [href('tours', s.ref_id), f ? f.title : s.ref_id]; }
    if (s.ref_type === 'glossary') return [href('glossary', s.ref_id), s.ref_id];
    return ['../' + s.ref_id.split('/').map((p) => encodeURIComponent(p)).join('/'), s.ref_id];
  }

  function startHere(id) {
    if (id) {
      const p = byId(M.paths, id);
      if (!p) return notFound('path', id);
      return `<p class="crumbs"><a href="${esc(href('paths'))}">Start here</a> / ${esc(p.title)}</p>
        <h1>${esc(p.title)}</h1><p class="lead">For: ${esc(p.audience)}</p>
        <ol class="steps">${p.steps.map((s, i) => { const [link, label] = stepTarget(s); return `<li class="step">
          <div class="step-num">${i + 1}</div><div class="step-body"><h3><a href="${esc(link)}">${esc(label)}</a></h3><p>${rich(s.note)}</p></div></li>`; }).join('')}</ol>`;
    }
    const n = M.agent_notes;
    return `<h1>Start here</h1><p class="lead">Pick the path that fits you.</p>
      <div class="cards">${M.paths.map((p) => `<a class="card link-card" href="${esc(href('paths', p.id))}"><h3>${esc(p.title)}</h3><p>${esc(p.audience)}</p></a>`).join('')}</div>
      <h2>For AI agents</h2>
      <p class="muted">The full machine-readable model is <code>explorer/data/model.json</code>. The repo root has <code>AGENTS.md</code>.</p>
      <h3>Rules</h3>${list(n.rules, rich)}
      <h3>Traps</h3>${list(n.traps, rich)}
      <h3>Do not touch</h3>${list(n.do_not_touch, (d) => `<code>${esc(d.path)}</code> — ${rich(d.reason)}`)}
      <h3>Commands</h3>${n.commands.map((c) => `<p class="muted">${esc(c.label)}</p><pre><code>${esc(c.command)}</code></pre>`).join('')}`;
  }

  let index = null;
  function buildIndex() {
    const out = [];
    const both = (o) => (o ? o.functional + ' ' + o.technical : '');
    const add = (kind, title, text, link) => out.push({ kind, title, text, link, hay: (title + ' ' + text).toLowerCase() });
    add('Project', M.project.name, M.project.tagline + ' ' + both(M.project.purpose), href('overview'));
    M.project.capabilities.forEach((c) => add('Capability', c.title, c.functional + ' ' + c.technical, href('overview')));
    M.architecture.components.forEach((c) => add('Component', c.name, both(c.description), href('architecture')));
    M.modules.forEach((m) => add('Module', m.name, [m.path, both(m.purpose), ...m.interface.map((i) => i.name + ' ' + i.description), ...m.invariants].join(' '), href('modules', m.id)));
    M.flows.forEach((f) => add('Tour', f.title, [both(f.summary), ...f.steps.map((s) => s.title + ' ' + both(s.text) + ' ' + s.file)].join(' '), href('tours', f.id)));
    M.glossary.forEach((g) => add('Term', g.term, g.definition, href('glossary', g.term)));
    return out;
  }
  function excerpt(text, term) {
    const at = Math.max(0, text.toLowerCase().indexOf(term));
    const start = Math.max(0, at - 60);
    return (start > 0 ? '…' : '') + text.slice(start, start + 160) + (start + 160 < text.length ? '…' : '');
  }
  function search(query) {
    const q = (query || '').trim();
    index = index || buildIndex();
    const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    const hits = terms.length ? index.filter((e) => terms.every((t) => e.hay.includes(t))) : [];
    const LIMIT = 100;
    const shown = hits.length > LIMIT ? ` (showing ${LIMIT} of ${hits.length})` : '';
    return `<h1>Search</h1><p class="muted">${hits.length} result${hits.length === 1 ? '' : 's'} for “${esc(q)}”${shown}</p>` +
      list(hits.slice(0, LIMIT), (h) => `<span class="tag">${esc(h.kind)}</span> <a href="${esc(h.link)}">${esc(h.title)}</a><div class="snippet">${esc(excerpt(h.text, terms[0]))}</div>`);
  }

  // ---- diagrams ------------------------------------------------------------
  let mermaidReady = false;
  // Mermaid 11.17 names a flowchart node `<renderId>-flowchart-<nodeId>-<n>` (11.4 dropped the
  // render id prefix). Strip the prefix we chose, then read the node id.
  function wireDiagram(holder, renderId) {
    holder.querySelectorAll('g.node').forEach((g) => {
      const raw = String(g.id || '');
      const local = raw.startsWith(renderId + '-') ? raw.slice(renderId.length + 1) : raw;
      const match = /^flowchart-(.+)-\d+$/.exec(local);
      if (!match) return;
      const comp = byId(M.architecture.components, match[1]);
      const moduleId = comp ? comp.module_ids[0] : (byId(M.modules, match[1]) ? match[1] : null);
      if (!moduleId && !comp) return;
      const go = () => {
        if (moduleId) { location.hash = href('modules', moduleId); return; }
        const card = document.getElementById('comp-' + comp.id);
        if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      };
      g.classList.add('clickable');
      g.setAttribute('tabindex', '0');
      g.setAttribute('role', 'link');
      g.addEventListener('click', go);
      g.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
    });
  }
  async function drawDiagrams() {
    const blocks = Array.from(view.querySelectorAll('.mermaid-src'));
    if (!blocks.length || !window.mermaid) return;
    if (!mermaidReady) {
      const dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      // `secure` lists config keys a diagram's own %%{init}%% directive or front-matter config may not
      // override. Mermaid's defaults are the first six; the styling keys are added because a
      // fontFamily or themeCSS value is pasted into the SVG's <style> and can load a URL.
      window.mermaid.initialize({
        startOnLoad: false, securityLevel: 'strict', suppressErrorRendering: true, theme: dark ? 'dark' : 'default',
        secure: ['secure', 'securityLevel', 'startOnLoad', 'maxTextSize', 'suppressErrorRendering', 'maxEdges',
          'theme', 'themeCSS', 'themeVariables', 'fontFamily', 'altFontFamily', 'darkMode', 'htmlLabels'],
      });
      mermaidReady = true;
    }
    for (let i = 0; i < blocks.length; i += 1) {
      const el = blocks[i];
      try {
        const renderId = 'dr-diagram-' + i + '-' + Date.now();
        const { svg } = await window.mermaid.render(renderId, el.textContent);
        const holder = document.createElement('div');
        holder.className = 'mermaid-out';
        holder.innerHTML = svg;
        el.replaceWith(holder);
        wireDiagram(holder, renderId);
      } catch (err) {
        el.insertAdjacentHTML('beforebegin', '<p class="warn">This diagram could not be drawn, so its source is shown.</p>');
        console.warn('[explorer] mermaid render failed', err);
      }
    }
  }

  // ---- router --------------------------------------------------------------
  // A Map, not a plain object: a route name comes from the URL, and a plain-object lookup would
  // also find inherited keys such as constructor, __proto__ and toString.
  const ROUTES = new Map([['overview', overview], ['architecture', architecture], ['modules', modules], ['tours', tours],
    ['glossary', glossary], ['paths', startHere], ['search', search]]);
  const NAV = [['overview', 'Overview'], ['architecture', 'Architecture'], ['modules', 'Modules'], ['tours', 'Tours'], ['glossary', 'Glossary'], ['paths', 'Start here']];
  const navEl = document.getElementById('nav');
  const searchEl = document.getElementById('search');
  const lensButtons = Array.from(document.querySelectorAll('[data-lens]'));

  function parseHash() {
    const raw = location.hash.replace(/^#\/?/, '');
    const [name, ...rest] = raw.split('/');
    let arg = null;
    try { arg = rest.length ? decodeURIComponent(rest.join('/')) : null; } catch (e) { arg = null; }
    return { name: ROUTES.has(name) ? name : 'overview', arg };
  }

  function render() {
    const { name, arg } = parseHash();
    navEl.querySelectorAll('a').forEach((a) => a.classList.toggle('active', a.dataset.route === name));
    lensButtons.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lens === lens)));
    const viewFn = ROUTES.get(name);
    const html = typeof viewFn === 'function' ? viewFn(arg) : null;
    // Only a string built by one of the views above ever reaches innerHTML.
    view.innerHTML = typeof html === 'string' ? html : overview();
    if (name === 'architecture') drawDiagrams();
    const anchor = name === 'glossary' && arg ? termAnchor(arg) : '';
    const target = anchor ? document.getElementById(anchor) : null;
    if (target) target.scrollIntoView({ block: 'center' }); else window.scrollTo(0, 0);
    if (document.activeElement !== searchEl) searchEl.value = name === 'search' ? (arg || '') : '';
  }

  document.title = M.project.name + ' · Project Explorer';
  document.getElementById('brand').textContent = M.project.name;
  navEl.innerHTML = NAV.map(([route, label]) => `<a href="${esc(href(route))}" data-route="${esc(route)}">${esc(label)}</a>`).join('');
  lensButtons.forEach((b) => b.addEventListener('click', () => {
    lens = b.dataset.lens === 'technical' ? 'technical' : 'functional';
    store.set(LENS_KEY, lens);
    render();
  }));
  let timer = 0;
  searchEl.addEventListener('input', () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      const value = searchEl.value.trim();
      location.hash = value ? '#/search/' + encodeURIComponent(value) : '#/overview';
    }, 150);
  });
  window.addEventListener('hashchange', render);
  render();
})();
