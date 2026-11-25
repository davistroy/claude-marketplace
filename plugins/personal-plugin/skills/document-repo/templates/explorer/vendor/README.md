# Vendored files

| File | Source | Licence |
|------|--------|---------|
| `mermaid.min.js` | `mermaid@11.17.2`, `dist/mermaid.min.js` from the npm registry via jsDelivr | MIT |

sha256: 581ed7d74bd9048d0e3a91363927d72ef22942d7722546b27f7cc29e35390eb8

Vendored so the explorer works offline and sends nothing to the network. To
upgrade: download the new `dist/mermaid.min.js`, update the version and sha256
above, then run `tests/test_explorer_template.py`. Open `#/architecture` in a
browser too: the page's Content-Security-Policy forbids `eval` and inline
scripts, so a build that needs either draws no diagrams.
