const { createRequire } = require('module');
const path = require('path');
const fs = require('fs');
const req = createRequire(path.join('C:/Users/1/.workbuddy/binaries/node/workspace/node_modules/@mdx-js/mdx/index.js'));
const { compile } = req('@mdx-js/mdx');

function walk(dir, acc) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, acc);
    else if (e.name.endsWith('.mdx')) acc.push(p);
  }
  return acc;
}

function stripFrontmatter(s) {
  if (s.startsWith('---')) {
    const i = s.indexOf('\n---', 3);
    if (i !== -1) return s.slice(i + 4);
  }
  return s;
}

(async () => {
  const root = process.argv[2] || 'commands/custom-commands';
  const files = walk(root, []);
  let bad = 0;
  for (const f of files) {
    const raw = fs.readFileSync(f, 'utf8');
    const body = stripFrontmatter(raw);
    try {
      await compile(body, { filepath: f });
    } catch (e) {
      bad++;
      console.log('FAIL ' + f);
      console.log('   ' + (e.message || e).split('\n')[0]);
    }
  }
  console.log(bad === 0 ? 'ALL_OK (' + files.length + ' files)' : ('FAILURES=' + bad));
})();
