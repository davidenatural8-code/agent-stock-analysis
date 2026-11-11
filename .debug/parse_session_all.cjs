// Full parse: iterate every zstd frame, emit all JSON lines, collect event types
// and show full structure of an assistant/message with usage (token counts)
const zlib = require('zlib');
const fs = require('fs');
const src = process.argv[2];
const dstRaw = process.argv.length > 3 ? process.argv[3] : process.env.TEMP + '\\session_full.jsonl';
const data = fs.readFileSync(src);

const magic = [0x28, 0xb5, 0x2f, 0xfd];
let offs = [];
for (let i = 0; i < data.length - 4; i++) {
  if (data[i] === magic[0] && data[i + 1] === magic[1] && data[i + 2] === magic[2] && data[i + 3] === magic[3]) {
    offs.push(i);
    i += 3;
  }
}
let fullText = [];
const types = {};
let usageSample = null;
let assistantCount = 0;
for (let f = 0; f < offs.length; f++) {
  const start = offs[f];
  const end = f + 1 < offs.length ? offs[f + 1] : data.length;
  try {
    const out = zlib.zstdDecompressSync(data.subarray(start, end)).toString('utf8');
    fullText.push(out);
    for (const line of out.split('\n')) {
      if (!line.trim()) continue;
      try {
        const o = JSON.parse(line);
        types[o.type] = (types[o.type] || 0) + 1;
        if (o.type === 'assistant/message') {
          assistantCount++;
          if (!usageSample) {
            const msg = o.data && o.data.message ? o.data.message : o.data;
            if (msg && (usageSeries(msg) || true)) {
              usageSample = o.data;
            }
          }
        }
      } catch (e) { /* skip line */ }
    }
  } catch (e) {
    // keep going
  }
}
function usageSeries(msg) { return true; }
fs.writeFileSync(dstRaw, fullText.join('\n'));
console.log('frames:', offs.length, 'full lines bytes:', fullText.join('').length);
console.log('EVENT TYPES:');
for (const [t, c] of Object.entries(types).sort((a, b) => b[1] - a[1])) console.log(' ', t, c);
console.log('assistant/message count:', assistantCount);
console.log('--- FULL sample assistant/message event ---');
console.log(JSON.stringify(usageSample, null, 1).slice(0, 3000));
console.log('WROTE:', dstRaw);
