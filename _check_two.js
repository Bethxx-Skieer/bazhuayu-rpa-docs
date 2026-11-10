const { createRequire } = require('module');
const path = require('path');
const fs = require('fs');
const req = createRequire(path.join('C:/Users/1/.workbuddy/binaries/node/workspace/node_modules/@mdx-js/mdx/index.js'));
const { compile } = req('@mdx-js/mdx');

(async () => {
  for (const f of ['commands/email/sendemailcommand.mdx','commands/email/logintomailboxcommand.mdx']) {
    let src = fs.readFileSync(path.join('C:/Users/1/Documents/bazhuayu-rpa-docs', f), 'utf8');
    src = src.replace(/^---[\s\S]*?---\n*/, '');
    try { await compile(src, { outputFormat: 'function-body' }); console.log('OK', f); }
    catch(e) { console.log('FAIL', f, e.message); process.exit(1); }
  }
})();
