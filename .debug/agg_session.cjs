// Aggregate usage from current workspace session + inspect request/header & model/selection
const zlib = require('zlib');
const fs = require('fs');
const src = process.argv[2];
const data = fs.readFileSync(src);
const magic = [0x28, 0xb5, 0x2f, 0xfd];
let offs = [];
for (let i = 0; i < data.length - 4; i++) {
  if (data[i] === magic[0] && data[i + 1] === magic[1] && data[i + 2] === magic[2] && data[i + 3] === magic[3]) {
    offs.push(i); i += 3;
  }
}
let inTot = 0, outTot = 0, steps = 0;
const models = {};
let reqSample = null, selSample = null, retrySample = null;
for (let f = 0; f < offs.length; f++) {
  const end = f + 1 < offs.length ? offs[f + 1] : data.length;
  try {
    const out = zlib.zstdDecompressSync(data.subarray(offs[f], end)).toString('utf8');
    for (const line of out.split('\n')) {
      if (!line.trim()) continue;
      let o; try { o = JSON.parse(line); } catch { continue; }
      if (o.type === 'assistant/message') {
        const m = o.data && o.data.message ? o.data.message : (o.data || {});
        const u = o.data.usage || o.usage || {};
        const prov = m.source && m.source.provider, mod = m.source && m.source.model;
        const key = (prov || '?') + ' | ' + (mod || '?');
        models[key] = models[key] || { steps: 0, input: 0, output: 0 };
        models[key].steps++; models[key].input += (u.inputTokens || 0); models[key].output += (u.outputTokens || 0);
        inTot += u.inputTokens || 0; outTot += u.outputTokens || 0; steps++;
      }
      if (o.type === 'request/header' && !reqSample) reqSample = o;
      if (o.type === 'model/selection' && !selSample) selSample = o;
      if ((o.type === 'llm/retry' || o.type === 'llm/retry-started') && !retrySample) retrySample = o;
    }
  } catch (e) {}
}
console.log('=== AGGREGATE BY MODEL ===');
for (const [k, v] of Object.entries(models)) console.log(k, JSON.stringify(v));
console.log('TOTAL steps:', steps, 'input:', inTot, 'output:', outTot, 'total:', inTot + outTot);
console.log('--- request/header sample ---'); console.log(JSON.stringify(reqSample, null, 1).slice(0, 1500));
console.log('--- model/selection sample ---'); console.log(JSON.stringify(selSample, null, 1).slice(0, 800));
console.log('--- llm/retry sample ---'); console.log(JSON.stringify(retrySample, null, 1).slice(0, 800));
