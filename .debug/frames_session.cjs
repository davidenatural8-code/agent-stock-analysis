// Try per-frame synchronous zstd decompression at each magic offset
const zlib = require('zlib');
const fs = require('fs');
const src = process.argv[2];
const data = fs.readFileSync(src);

const magic = [0x28, 0xb5, 0x2f, 0xfd];
let offs = [];
for (let i = 0; i < data.length - 4; i++) {
  if (data[i] === magic[0] && data[i + 1] === magic[1] && data[i + 2] === magic[2] && data[i + 3] === magic[3]) {
    offs.push(i);
    i += 3;
  }
}
console.log('total magic offsets:', offs.length);

for (let f = 0; f < Math.min(5, offs.length - 1); f++) {
  const start = offs[f];
  const end = offs[f + 1];
  const blob = data.subarray(start, end);
  try {
    const out = zlib.zstdDecompressSync(blob);
    const text = out.toString('utf8');
    console.log(`frame ${f} @${start} OK -> ${out.length} bytes: ${text.slice(0, 150).replace(/\n/g, '\\n')}`);
  } catch (e) {
    console.log(`frame ${f} @${start} FAIL: ${e.code || e.message.slice(0, 80)}`);
    // print the frame header bytes for inspection
    let h = '';
    for (let i = start; i < start + 24; i++) h += data[i].toString(16).padStart(2, '0') + ' ';
    console.log('  header:', h);
  }
}
// last frame -> EOF
const last = offs[offs.length - 1];
try {
  const out = zlib.zstdDecompressSync(data.subarray(last));
  console.log(`last frame @${last} OK -> ${out.length} bytes: ${out.toString('utf8').slice(0, 150).replace(/\n/g, '\\n')}`);
} catch (e) {
  console.log(`last frame @${last} FAIL: ${e.code || e.message.slice(0, 80)}`);
}
