// Stream-decompress a DSH session.v4.jsonl.zstd (concatenated zstd frames) to plain JSONL
const zlib = require('zlib');
const fs = require('fs');

const src = process.argv[2];
const dst = process.env.TEMP + '\\session_dump.jsonl';

console.log('zlib.createZstdDecompress:', typeof zlib.createZstdDecompress);
if (typeof zlib.createZstdDecompress !== 'function') process.exit(2);

const dec = zlib.createZstdDecompress();
const input = fs.createReadStream(src);
const output = fs.createWriteStream(dst);
let bytes = 0;
dec.on('data', (c) => (bytes += c.length));
dec.on('error', (e) => { console.error('STREAM ERROR:', e.code || e.message); process.exit(1); });
output.on('finish', () => {
  const out = fs.readFileSync(dst, 'utf8');
  const lines = out.split('\n').filter((l) => l.trim());
  console.log('decompressed bytes:', bytes, 'lines:', lines.length);
  let sample = lines.length > 1 ? JSON.parse(lines[1]) : null;
  if (sample) console.log('LINE1 KEYS:', Object.keys(sample).join(','));
  console.log('DUMPED TO:', dst);
});
input.pipe(dec).pipe(output);
