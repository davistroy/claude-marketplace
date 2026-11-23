// Re-print a JS/TS file with every comment removed, using the TypeScript compiler named by the
// caller. Two versions of a file that print the same differ only in comments and formatting.
//
// The script kind comes from the file name, so the file is parsed as TypeScript
// itself would parse it: `<T>x` is an assertion in .ts/.mts/.cts but JSX in
// .tsx, and .js/.jsx/.mjs/.cjs are parsed as JavaScript with JSX. An extension
// this table does not know is an error, never a guess.
//
// The compiler is never searched for. The caller passes an ordered list of candidates and the
// first one that holds a typescript package is loaded; nothing walks up from a candidate, so a
// stray node_modules above the repository cannot be picked up (see findTypescript).
//
// Usage: node ts_print.js <candidates-json> <before-file> <after-file> <virtual-name>
// Prints JSON {equal, before_errors, after_errors, version}; `version` is the compiler's own.
// Exit 0 = printed, 2 = could not print (message on stderr), 3 = typescript not found.
'use strict';
const fs = require('fs');
const path = require('path');

const EXIT_FAILED = 2;
const EXIT_NOT_FOUND = 3;

function isDirectory(dir) {
  try {
    return fs.statSync(dir).isDirectory();
  } catch (err) {
    return false;
  }
}

function isTypescriptPackage(dir) {
  try {
    const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
    return manifest !== null && manifest.name === 'typescript';
  } catch (err) {
    return false;
  }
}

// The package directory a candidate names, or null. A candidate is one of:
//   a project directory           <candidate>/node_modules/typescript
//   a node_modules directory      <candidate>/typescript   (the global npm root is one)
//   the package directory itself  <candidate>              (its package.json says "typescript")
// Each is looked at once, exactly where it is written. There is no walk up to a parent.
function packageDirOf(candidate) {
  const nested = path.join(candidate, 'node_modules', 'typescript');
  if (isDirectory(nested)) return nested;
  if (path.basename(candidate) === 'node_modules') {
    const sibling = path.join(candidate, 'typescript');
    if (isDirectory(sibling)) return sibling;
  }
  return isTypescriptPackage(candidate) ? candidate : null;
}

function findTypescript(candidates) {
  for (const candidate of candidates) {
    const dir = packageDirOf(path.resolve(candidate));
    if (dir !== null) return dir;
  }
  return null;
}

// Layout the parser records but the printer honours, none of it code:
//  - An empty block prints "{ }" or "{\n}" by a flag (and, for a function body or a module
//    block, by whether the source braces share a line), and a comment inside makes the braces
//    span lines. Every empty block is replaced by one fresh, empty, multi-line block.
//  - JSX children. `{/* c */}` is a JsxExpression with no expression, which the compiler
//    discards, so it is removed. A JsxText is not printed as its source: JSX cooks whitespace per
//    text node (see cookJsxText), so a comment that splits one text into two can change what
//    renders while the source characters around it stay the same ("Hello\n  world" renders
//    "Hello world"; "Hello{/* c */}\n  world" renders "Hello", "world"). Each JsxText is replaced
//    by one child holding its cooked value, node by node, and a text that cooks to nothing is
//    removed. A comment alone on its own line between elements then normalises away, and one
//    that changes the rendered children fails.

// What a JSX compiler makes of one text node's raw source, as the strings that would be its
// child. Compilers differ at the edges, so the value is cooked by each rule and both are kept:
//  - TypeScript (fixupWhitespaceAndDecodeEntities): split on line breaks; drop lines that are
//    all whitespace; trim each line except at the start of the first and the end of the last;
//    join with one space. Its own isLineBreak and isWhiteSpaceSingleLine decide the characters.
//  - Babel (cleanJSXElementLiteralChild, followed by esbuild and swc): the same shape, but only
//    "\r\n", "\n" and "\r" break lines, only space and tab are whitespace, and a tab becomes a
//    space.
// Entities are not decoded: an edit that only re-spells one fails, which is safe. Because Babel
// decodes before it splits lines, a text that holds "&" also keeps its raw source, so an entity
// that decodes to whitespace cannot hide a change. Two texts are equal only if every rule
// agrees, so when the compilers disagree about a change, the change fails.
function cookTypescript(ts, text) {
  let acc;
  let first = 0;
  let last = -1;
  const add = (line) => {
    acc = acc === undefined ? line : `${acc} ${line}`;
  };
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    if (ts.isLineBreak(c)) {
      if (first !== -1 && last !== -1) add(text.substr(first, last - first + 1));
      first = -1;
    } else if (!ts.isWhiteSpaceSingleLine(c)) {
      last = i;
      if (first === -1) first = i;
    }
  }
  if (first !== -1) add(text.substr(first));
  return acc === undefined ? '' : acc;
}

function cookBabel(text) {
  const lines = text.split(/\r\n|\n|\r/);
  let lastNonEmpty = 0;
  lines.forEach((line, i) => {
    if (/[^ \t]/.test(line)) lastNonEmpty = i;
  });
  let out = '';
  lines.forEach((line, i) => {
    let trimmed = line.replace(/\t/g, ' ');
    if (i !== 0) trimmed = trimmed.replace(/^[ ]+/, '');
    if (i !== lines.length - 1) trimmed = trimmed.replace(/[ ]+$/, '');
    if (trimmed) out += i === lastNonEmpty ? trimmed : `${trimmed} `;
  });
  return out;
}

function cookJsxText(ts, text) {
  const cooked = [cookTypescript(ts, text), cookBabel(text)];
  if (cooked.every((value) => value === '')) return null;
  if (text.includes('&')) cooked.push(text);
  return cooked;
}

function normalise(ts, sourceFile) {
  const factory = ts.factory;
  // A JSX child as it compiles: null when the compiler drops it, otherwise the child itself or,
  // for text, one expression child holding the cooked values.
  const jsxChild = (child) => {
    if (ts.isJsxExpression(child)) {
      return !child.expression && !child.dotDotDotToken ? null : child;
    }
    if (!ts.isJsxText(child)) return child;
    const cooked = cookJsxText(ts, child.text);
    if (cooked === null) return null;
    const values = cooked.map((value) => factory.createStringLiteral(value));
    return factory.createJsxExpression(undefined, factory.createArrayLiteralExpression(values));
  };
  const transformer = (context) => {
    const visit = (original) => {
      const node = ts.visitEachChild(original, visit, context);
      if (ts.isBlock(node) && node.statements.length === 0) return factory.createBlock([], true);
      if (ts.isModuleBlock(node) && node.statements.length === 0) return factory.createModuleBlock([]);
      if (ts.isJsxElement(node) || ts.isJsxFragment(node)) {
        // Every text is cooked on the children as written, before any comment is removed, so a
        // text split by a comment stays two children.
        const kept = node.children.map(jsxChild).filter((child) => child !== null);
        return ts.isJsxElement(node)
          ? factory.updateJsxElement(node, node.openingElement, kept, node.closingElement)
          : factory.updateJsxFragment(node, node.openingFragment, kept, node.closingFragment);
      }
      return node;
    };
    return visit;
  };
  const result = ts.transform(sourceFile, [transformer]);
  try {
    return result.transformed[0];
  } finally {
    result.dispose();
  }
}

function main() {
  const [, , candidatesJson, beforePath, afterPath, name] = process.argv;
  const candidates = JSON.parse(candidatesJson);
  if (!Array.isArray(candidates) || !candidates.every((c) => typeof c === 'string')) {
    throw new Error('candidates must be a JSON array of directory paths');
  }
  const location = findTypescript(candidates);
  if (location === null) {
    process.stdout.write(JSON.stringify({ error: 'typescript-not-found' }));
    return EXIT_NOT_FOUND;
  }
  let ts;
  try {
    ts = require(location);
  } catch (err) {
    // The first compiler found is the one that runs. A broken install is an error, not a cue to
    // try the next candidate, which would make the result depend on what else is installed.
    throw new Error(`cannot load typescript from ${location}: ${err && err.message ? err.message : err}`);
  }

  const kinds = new Map([
    ['.ts', ts.ScriptKind.TS],
    ['.mts', ts.ScriptKind.TS],
    ['.cts', ts.ScriptKind.TS],
    ['.tsx', ts.ScriptKind.TSX],
    ['.js', ts.ScriptKind.JS],
    ['.mjs', ts.ScriptKind.JS],
    ['.cjs', ts.ScriptKind.JS],
    ['.jsx', ts.ScriptKind.JSX],
  ]);
  const kind = kinds.get(path.extname(name).toLowerCase());
  if (kind === undefined) {
    process.stderr.write(`unsupported file type: ${name}\n`);
    return EXIT_FAILED;
  }

  // newLine is fixed so the output never depends on the platform's default.
  const printer = ts.createPrinter({ removeComments: true, newLine: ts.NewLineKind.LineFeed });

  function print(file) {
    const text = fs.readFileSync(file, 'utf8');
    // `name` keeps its .d.ts / .d.mts suffix, which is how TypeScript knows a file is ambient.
    const sf = ts.createSourceFile(name, text, ts.ScriptTarget.Latest, true, kind);
    if (!Array.isArray(sf.parseDiagnostics)) {
      throw new Error(`typescript ${ts.version} does not expose parseDiagnostics`);
    }
    return { text: printer.printFile(normalise(ts, sf)), errors: sf.parseDiagnostics.length };
  }

  const a = print(beforePath);
  const b = print(afterPath);
  process.stdout.write(
    JSON.stringify({
      equal: a.text === b.text,
      before_errors: a.errors,
      after_errors: b.errors,
      version: ts.version,
    }),
  );
  return 0;
}

try {
  process.exitCode = main();
} catch (err) {
  process.stderr.write(`${err && err.stack ? err.stack : err}\n`);
  process.exitCode = EXIT_FAILED;
}
