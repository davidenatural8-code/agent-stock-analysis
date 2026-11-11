// Hexdump start of session file and detect structure: magic markers, plain text chunks
const fs = require('fs');
const data = fs.readFileSync(process.argv[2]);
console.log('FILE SIZE:', data.length);
function hex(buf, off, len) {
  let s = '';
  for (let i = off; i < Math.min(off + len, buf.length); i++) {
    const b = buf[i];
    s += b.toString(16).padStart(2, '0') + ' ';
  }
  return s;
}
console.log('first 64 bytes :', hex(data, 0, 64));
console.log('bytes  256-320 :', hex(data, 256, 64));
console.log('bytes 16384-16448:', hex(data, 16384, 64));
// search magic FD2FB528 LE = 28 B5 2F FD at later offsets
const MAGIC = Buffer.from([0x28, 0xb5, 0x2f, 0xfd]);
let found = [];
for (let i = 0; i < data.length - 4; i++) {
  if (data[i] === 0x28 && data[i + 1] === 0xb5 && data[i + 2] === 0x2f && data[i + 3] === 0xfd) found.push(i);
  if (found.length > 20) break;
}
console.log('zstd magic offsets (first 20):', found.join(', '));
// check for plain-text content in the tail
const tail = data.subarray(data.length - 400);
console.log('tail as utf8 (first 400):', tail.toString('utf8').replace(/\n/g, '\\n').slice(0, 400));
const mid = data.subarray(Math.floor(data.length / 2), Math.floor(data.length / 2) + 400);
console.log('mid as utf8 (400):', mid.toString('utf8').replace(/\n/g, '\\n').slice(0, 400));
