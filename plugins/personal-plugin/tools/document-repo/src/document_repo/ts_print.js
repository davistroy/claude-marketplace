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
//  - JSX children the compiler discards: `{/* c */}` is a JsxExpression with no expression, and
//    a whitespace-only text that contains a line break is dropped by JSX. A comment on its own
//    line between two elements splits one such text into two, so both kinds are removed.
//    Text that is not removed (words, or whitespace on one line) is meaningful and stays.
const DROPPED_JSX_TEXT = /^[ \t]*[\r\n][ \t\r\n]*$/;

function normalise(ts, sourceFile) {
  const factory = ts.factory;
  const discarded = (child) => {
    if (ts.isJsxExpression(child)) return !child.expression && !child.dotDotDotToken;
    return ts.isJsxText(child) && DROPPED_JSX_TEXT.test(child.text);
  };
  const transformer = (context) => {
    const visit = (original) => {
      const node = ts.visitEachChild(original, visit, context);
      if (ts.isBlock(node) && node.statements.length === 0) return factory.createBlock([], true);
      if (ts.isModuleBlock(node) && node.statements.length === 0) return factory.createModuleBlock([]);
      if (ts.isJsxElement(node) || ts.isJsxFragment(node)) {
        const kept = node.children.filter((child) => !discarded(child));
        if (kept.length === node.children.length) return node;
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
