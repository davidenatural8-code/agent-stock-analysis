const fs = require('fs');
const raw = fs.readFileSync(process.argv[2], 'utf8').replace(/\r?\n/g, ' ');
const truncIdx = raw.indexOf('(Content truncated');
const body = truncIdx >= 0 ? raw.slice(0, truncIdx) : raw;
const startIndex = body.indexOf('{"data":[');
console.log('rawlen', raw.length, 'truncIdx', truncIdx, 'startIndex', startIndex);
const arrStart = startIndex + 10;
console.log('at arrStart:', JSON.stringify(body.slice(arrStart, arrStart + 80)));
let depth = 1, inStr = false, esc = false, closed = 0, opened = 0;
for (let i = arrStart; i < body.length; i++) {
  const c = body[i];
  if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === '"') inStr = false; continue; }
  if (c === '"') { inStr = true; continue; }
  if (c === '{') { opened++; depth++; }
  else if (c === '}') { closed++; depth--; if (depth === 1) closed; }
  else if (c === ']') { if (depth === 1) { console.log('ARRAY END at i=', i, 'opened', opened, 'closed', closed); break; } depth--; }
}
console.log('final opened', opened, 'closed', closed, 'depth', depth);
