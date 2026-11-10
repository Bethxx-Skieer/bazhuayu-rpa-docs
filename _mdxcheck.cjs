const { createRequire } = require('module');
const path = require('path');
const fs = require('fs');
const req = createRequire(path.join('C:/Users/1/.workbuddy/binaries/node/workspace/node_modules/@mdx-js/mdx/index.js'));
const { compile } = req('@mdx-js/mdx');

const files = process.argv.slice(2);

function stripFrontmatter(s) {
  if (s.startsWith('---')) {
    const i = s.indexOf('\n---', 3);
    if (i !== -1) {
      return s.slice(i + 4);
    }
  }
  return s;
}

(async () => {
  let bad = 0;
  for (const f of files) {
    const raw = fs.readFileSync(f, 'utf8');
    const body = stripFrontmatter(raw);
    try {
      await compile(body, { filepath: f });
      console.log('OK   ' + f);
    } catch (e) {
      bad++;
      console.log('FAIL ' + f);
      console.log('   ' + (e.message || e).split('\n')[0]);
    }
  }
  console.log(bad === 0 ? 'ALL_OK' : ('FAILURES=' + bad));
})();
