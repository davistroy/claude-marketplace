// Re-print a JS/TS file with every comment removed, using the TypeScript compiler named by the
// caller. Two versions of a file that print the same differ only in comments and formatting.
//
// The script kind comes from the file name, so the file is parsed as TypeScript
// itself would parse it: `<T>x` is an assertion in .ts/.mts/.cts but JSX in
// .tsx, and .js/.jsx/.mjs/.cjs are parsed as JavaScript with JSX. An extension
// this table does not know is an error, never a guess.
//
// The compiler is never searched for. The caller passes an ordered list of candidates and the
// first one that holds the pinned typescript package is loaded; nothing walks up from a
// candidate, so a stray node_modules above the repository cannot be picked up (see
// findTypescript). "Pinned" means package.json says name "typescript" and version TS_VERSION,
// and lib/typescript.js hashes to TS_SHA256 (SEC-01). A candidate that fails any check is
// skipped without running a line of it. The hashed bytes are the bytes that run: they are read
// once and compiled here, with a require that serves only Node built-ins, so neither the
// package's "main" nor anything else on disk can substitute other code.
//
// Usage: node ts_print.js <candidates-json> <before-file> <after-file> <virtual-name>
// Prints JSON {equal, before_errors, after_errors, version, location}; `version` is the
// compiler's own and `location` the package directory it was loaded from.
// Exit 0 = printed, 2 = could not print (message on stderr), 3 = typescript not found.
'use strict';
const crypto = require('crypto');
const fs = require('fs');
const Module = require('module');
const path = require('path');
const vm = require('vm');

const EXIT_FAILED = 2;
const EXIT_NOT_FOUND = 3;

// Mirrored in verify.py (TS_VERSION, TS_SHA256); a test keeps the two in step. npm tarballs are
// deterministic, so every install of this version holds exactly these bytes.
const TS_VERSION = '5.6.3';
const TS_SHA256 = 'f316520790d4db220a10d890c5f85310e26a1bd3c104b8d3b5eb62ba0491651b';

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

// Why the package at `dir` is not the pinned compiler, or null when it is. On success the
// verified source is stored in `found.source`, so the bytes hashed are the bytes compiled.
function untrusted(dir, found) {
  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
  } catch (err) {
    return 'unreadable package.json';
  }
  if (manifest === null || typeof manifest !== 'object') return 'unreadable package.json';
  if (manifest.name !== 'typescript') return `package name ${JSON.stringify(manifest.name)}`;
  if (manifest.version !== TS_VERSION) {
    return `version ${JSON.stringify(manifest.version)}, need ${TS_VERSION}`;
  }
  const file = path.join(dir, 'lib', 'typescript.js');
  let source;
  try {
    source = fs.readFileSync(file);
  } catch (err) {
    return 'no lib/typescript.js';
  }
  const digest = crypto.createHash('sha256').update(source).digest('hex');
  if (digest !== TS_SHA256) return `lib/typescript.js sha256 ${digest} is not the pinned one`;
  found.file = file;
  found.source = source.toString('utf8');
  return null;
}

// The first candidate that holds the pinned compiler, as {dir, file, source}, or null. Every
// candidate that holds some other package is reported on stderr and skipped.
function findTypescript(candidates) {
  for (const candidate of candidates) {
    const dir = packageDirOf(path.resolve(candidate));
    if (dir === null) continue;
    const found = { dir };
    const why = untrusted(dir, found);
    if (why === null) return found;
    process.stderr.write(`skipped typescript at ${dir}: ${why}\n`);
  }
  return null;
}

// Run the verified compiler source as a CommonJS module. Its require serves Node built-ins only:
// the compiler needs nothing else to parse and print, and a lookup on disk could load a module
// the target repository controls (lib/typescript.js tries "source-map-support", for one).
function loadCompiler(found) {
  const builtins = new Set(Module.builtinModules);
  const onlyBuiltins = (id) => {
    if (builtins.has(id.replace(/^node:/, ''))) return require(id);
    throw new Error(`module ${id} is not a Node built-in`);
  };
  const module = { exports: {} };
  const params = ['exports', 'require', 'module', '__filename', '__dirname'];
  const fn = vm.compileFunction(found.source, params, { filename: found.file });
  fn.call(module.exports, module.exports, onlyBuiltins, module, found.file, path.dirname(found.file));
  return module.exports;
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
//    by one marker holding its cooked value (encodeJsxText), node by node, and a text that cooks
//    to nothing is removed. A comment alone on its own line between elements then normalises
//    away, and one that changes the rendered children fails.

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

// The printed form of a cooked text. It must be something no parseable source prints, or an edit
// that turns text into code (`Hello` into `{["Hello", "Hello"]}`) would print the same and pass.
// It is printed as JSX text that starts with "<#": source JSX text cannot hold "<" (it opens a
// tag), and a tag name cannot start with "#" (that is a parse error, and a file with one fails).
// The JSON inside has every "<", ">", "{", "}" and "&" escaped, so it cannot close the marker
// early or read as markup, and each text node stays one marker.
function encodeJsxText(cooked) {
  const json = JSON.stringify(cooked).replace(
    /[<>{}&]/g,
    (c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, '0')}`,
  );
  return `<#text ${json}>`;
}

function normalise(ts, sourceFile) {
  const factory = ts.factory;
  // A JSX child as it compiles: null when the compiler drops it, otherwise the child itself or,
  // for text, one marker holding the cooked values.
  const jsxChild = (child) => {
    if (ts.isJsxExpression(child)) {
      return !child.expression && !child.dotDotDotToken ? null : child;
    }
    if (!ts.isJsxText(child)) return child;
    const cooked = cookJsxText(ts, child.text);
    return cooked === null ? null : factory.createJsxText(encodeJsxText(cooked), false);
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
  const found = findTypescript(candidates);
  if (found === null) {
    process.stdout.write(JSON.stringify({ error: 'typescript-not-found' }));
    return EXIT_NOT_FOUND;
  }
  let ts;
  try {
    ts = loadCompiler(found);
  } catch (err) {
    // The first pinned compiler found is the one that runs. One that fails to load is an error,
    // not a cue to try the next candidate, which would make the result depend on what else is
    // installed.
    const why = err && err.message ? err.message : err;
    throw new Error(`cannot load typescript from ${found.dir}: ${why}`);
  }
  if (ts.version !== TS_VERSION) {
    throw new Error(`typescript at ${found.dir} reports version ${ts.version}, need ${TS_VERSION}`);
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
      location: found.dir,
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
