// Inspect the structure of the dumped session JSON (single line) for token usage info
const fs = require('fs');
const dst = process.env.TEMP + '\\session_dump.jsonl';
const raw = fs.readFileSync(dst, 'utf8');
const o = JSON.parse(raw);
console.log('TOP KEYS:', Object.keys(o).join(','));
console.log('top-level token-ish keys:', Object.keys(o).filter(k => /token|usage|cost/i.test(k)));
for (const k of Object.keys(o)) {
  const v = o[k];
  if (Array.isArray(v)) {
    console.log('ARRAY', k, 'length', v.length, 'first-item keys:', v.length ? Object.keys(v[0]).join(',') : '(empty)');
  }
}
// deep scan for keys matching tokens anywhere (limit depth)
function scan(obj, path, depth) {
  if (depth > 6 || obj === null || typeof obj !== 'object') return;
  for (const k of Object.keys(obj)) {
    if (/token|usage|cost|cache/i.test(k)) console.log('HIT:', path + '.' + k, '=', String(JSON.stringify(obj[k])).slice(0, 200));
    if (obj[k] && typeof obj[k] === 'object' && !(obj[k] instanceof Array)) scan(obj[k], path + '.' + k, depth + 1);
  }
}
scan(o, 'root', 0);
