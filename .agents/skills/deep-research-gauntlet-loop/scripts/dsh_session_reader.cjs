// dsh_session_reader.cjs — Lector de sesiones DeepSeek Harness (.dsh/sessions/**/session.v4.jsonl.zstd)
// El archivo es un flujo de FRAMES zstd concatenados; cada frame contiene 1..N eventos JSONL.
// Salida: JSONL compacto con usage de LLM por paso.
//
// Uso: node dsh_session_reader.cjs <session.v4.jsonl.zstd> --out <salida.jsonl> [--all-events]

const zlib = require('zlib');
const fs = require('fs');
const path = require('path');

function readFrames(buf) {
  const MAGIC = [0x28, 0xb5, 0x2f, 0xfd];
  const offs = [];
  for (let i = 0; i < buf.length - 4; i++) {
    if (buf[i] === MAGIC[0] && buf[i + 1] === MAGIC[1] && buf[i + 2] === MAGIC[2] && buf[i + 3] === MAGIC[3]) {
      offs.push(i);
      i += 3; // skip after the 4 magic bytes
    }
  }
  const out = [];
  for (let f = 0; f < offs.length; f++) {
    const start = offs[f];
    const end = f + 1 < offs.length ? offs[f + 1] : buf.length;
    try {
      out.push(zlib.zstdDecompressSync(buf.subarray(start, end)).toString('utf8'));
    } catch (e) {
      out.push(''); // corrupted/noise frame: skip
    }
  }
  return out;
}

function main() {
  const args = process.argv.slice(2);
  const src = args[0];
  const oIdx = args.indexOf('--out');
  const outPath = oIdx >= 0 ? args[oIdx + 1] : null;
  const allEvents = args.includes('--all-events');
  if (!src || !outPath) {
    console.error('usage: node dsh_session_reader.cjs <session.v4.jsonl.zstd> --out <file.jsonl> [--all-events]');
    process.exit(2);
  }
  const buf = fs.readFileSync(src);
  const sessionDirName = path.basename(path.dirname(src));
  const sessionId = sessionDirName.startsWith('session-') ? sessionDirName.slice(8) : sessionDirName;

  const events = [];
  for (const frame of readFrames(buf)) {
    for (const line of frame.split('\n')) {
      if (!line.trim()) continue;
      let o;
      try { o = JSON.parse(line); } catch { continue; }
      if (o.type === 'session') {
        events.push({ t: 'session', sessionId, time: o.createdAt || null, cwd: o.cwd || null, parentSession: o.parentSession || null });
      } else if (o.type === 'assistant/message' && o.data) {
        const m = o.data.message || {};
        const u = o.data.usage || {};
        const src_ = m.source || {};
        events.push({
          t: 'llm_step',
          sessionId,
          seq: o.seq ?? null,
          time: o.time ?? null,
          provider: src_.provider || null,
          model: src_.model || null,
          turn: o.data.turn ?? null,
          step: o.data.step ?? null,
          inputTokens: u.inputTokens ?? 0,            // input FRESCO (no cacheado)
          cacheReadTokens: u.cacheReadTokens ?? 0,    // aciertos de prompt-cache (prefix)
          outputTokens: u.outputTokens ?? 0,
          totalTokens: u.totalTokens ?? ((u.inputTokens || 0) + (u.outputTokens || 0) + (u.cacheReadTokens || 0)),
        });
      } else if (o.type === 'llm/retry') {
        events.push({ t: 'llm_retry', sessionId, time: o.time ?? null, provider: o.data?.provider || null, failure: o.data?.failure?.code || null });
      } else if (o.type === 'compaction/start' || o.type === 'compaction/end') {
        events.push({ t: o.type.replace('/', '_'), sessionId, time: o.time ?? null });
      } else if (allEvents) {
        events.push({ t: o.type, sessionId, seq: o.seq ?? null, time: o.time ?? null });
      }
    }
  }
  fs.writeFileSync(outPath, events.map((e) => JSON.stringify(e)).join('\n') + '\n');
  console.log('events:', events.length, '->', outPath);
}

main();
