// Streaming-scan complete model objects from a truncated/double-escaped OpenRouter dump
const fs = require('fs');
let raw = fs.readFileSync(process.argv[2], 'utf8').replace(/\r?\n/g, ' ');
const truncIdx = raw.indexOf('(Content truncated');
raw = truncIdx >= 0 ? raw.slice(0, truncIdx) : raw;
// unescape: the dump is presented as a JSON string (\" etc.)
if (raw.includes('\\"')) raw = raw.replace(/\\"/g, '"').replace(/\\\\/g, '\\');
const startIndex = raw.indexOf('{"data":[');
if (startIndex < 0) { console.error('no start'); process.exit(1); }
const arrStart = startIndex + '{"data":['.length;

const re = [/^z-ai\/glm-5/, /^deepseek\/deepseek-v4/, /^anthropic\/claude-/, /^openai\/gpt-/, /^google\/gemini-/, /^moonshotai\/kimi-k/, /^minimax\/minimax-m/, /^x-ai\/grok/, /^qwen\/qwen3\.8-max/];
let i = arrStart, depth = 1, objStart = -1, inStr = false, esc = false;
const objects = [];
while (i < raw.length && objects.length < 800) {
  const c = raw[i];
  if (inStr) {
    if (esc) esc = false;
    else if (c === '\\') esc = true;
    else if (c === '"') inStr = false;
    i++; continue;
  }
  if (c === '"') { inStr = true; i++; continue; }
  if (c === '{') { if (depth === 1) objStart = i; depth++; i++; continue; }
  if (c === '[') { depth++; i++; continue; }
  if (c === '}') { depth--; if (depth === 1 && objStart >= 0) { objects.push(raw.slice(objStart, i + 1)); objStart = -1; } i++; continue; }
  if (c === ']') { if (depth === 1) break; depth--; i++; continue; }
  i++;
}
const rows = [];
for (const t of objects) {
  let m; try { m = JSON.parse(t); } catch { continue; }
  if (m && m.id && m.pricing && m.pricing.prompt != null) {
    rows.push({
      id: m.id, name: m.name, ctx: m.context_length,
      p_in: m.pricing.prompt, p_out: m.pricing.completion,
      p_cache: m.pricing.input_cache_read ?? null, p_cache_w: m.pricing.input_cache_write ?? null,
    });
  }
}
const seen = new Set();
const uniq = rows.filter((o) => (seen.has(o.id) ? false : (seen.add(o.id), true)));
const sel = uniq.filter((o) => re.some((r) => r.test(o.id)) && !o.id.endsWith(':batch'));
const dst = process.env.PROJ_DIR + '\\prices_extracted.json';
fs.writeFileSync(dst, JSON.stringify(sel, null, 1));
console.log('OBJECTS PARSED:', objects.length, 'MODEL ROWS:', uniq.length, 'CANDIDATE ROWS:', sel.length, '->', dst);
