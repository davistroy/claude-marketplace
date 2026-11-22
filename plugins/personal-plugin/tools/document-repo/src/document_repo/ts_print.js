// Re-print a JS/TS file with every comment removed, using the TypeScript
// compiler found in the target repo (or a global install). Two versions of a
// file that print the same differ only in comments and formatting.
//
// The script kind comes from the file name, so the file is parsed as TypeScript
// itself would parse it: `<T>x` is an assertion in .ts/.mts/.cts but JSX in
// .tsx, and .js/.jsx/.mjs/.cjs are parsed as JavaScript with JSX. An extension
// this table does not know is an error, never a guess.
//
// Usage: node ts_print.js <search-paths-json> <before-file> <after-file> <virtual-name>
// Prints JSON {equal, before_errors, after_errors}.
// Exit 0 = printed, 2 = could not print (message on stderr), 3 = typescript not found.
'use strict';
const fs = require('fs');
const path = require('path');

const EXIT_FAILED = 2;
const EXIT_NOT_FOUND = 3;

function main() {
  const [, , pathsJson, beforePath, afterPath, name] = process.argv;
  let ts;
  try {
    ts = require(require.resolve('typescript', { paths: JSON.parse(pathsJson) }));
  } catch (err) {
    process.stdout.write(JSON.stringify({ error: 'typescript-not-found' }));
    return EXIT_NOT_FOUND;
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
    return { text: printer.printFile(sf), errors: sf.parseDiagnostics.length };
  }

  const a = print(beforePath);
  const b = print(afterPath);
  process.stdout.write(
    JSON.stringify({ equal: a.text === b.text, before_errors: a.errors, after_errors: b.errors }),
  );
  return 0;
}

try {
  process.exitCode = main();
} catch (err) {
  process.stderr.write(`${err && err.stack ? err.stack : err}\n`);
  process.exitCode = EXIT_FAILED;
}
