import { compile } from '@mdx-js/mdx';
import fs from 'fs';
import path from 'path';

const REPO = "C:/Users/1/Documents/bazhuayu-rpa-docs";
const slugs = "gettaskstatuscommand getemailscommand regexmatchcommand setvariablecommand batchinserttodatabasecommand connecttodatabasecommand querydatabasecommand getgooglecredentialcommand getgooglespreadsheetcommand recognizecaptchabyprovidercommand recognizecharactercommand recognizegeneraltextcommand recognizeinvoicecommand recognizerecaptchav2command recognizerotationcommand recognizeslidercommand recognizesliderpuzzlecommand recognizetablecommand recognizetextclickcommand recognizetrajectorycommand readlarkspreadsheetcommand".split(/\s+/);

const map = {};
function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p);
    else if (e.name.endsWith('.mdx')) map[e.name.replace(/\.mdx$/, '')] = p;
  }
}
walk(path.join(REPO, "commands"));
console.error("DEBUG map size:", Object.keys(map).length, "has gettaskstatuscommand:", !!map["gettaskstatuscommand"]);

let fail = [];
for (const slug of slugs) {
  console.error("DBG slug=", JSON.stringify(slug), "hit=", !!map[slug]);
  const mfp = map[slug];
  if (!mfp) { console.log("MISSING MDX", slug); fail.push(slug); continue; }
  let txt = fs.readFileSync(mfp, "utf-8").replace(/^---\n[\s\S]*?\n---\n/, "");
  try { await compile(txt, { outputFormat: 'function-body' }); }
  catch (e) { console.log("COMPILE FAIL", slug, ":", String(e.message).split("\n")[0]); fail.push(slug); }
}
console.log(fail.length ? `\nFAILED: ${fail.join(", ")}` : "\nALL 21 COMPILE OK");
