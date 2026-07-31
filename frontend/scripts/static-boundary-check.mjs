import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const roots = ['components', 'services', 'types'];
const forbidden = [
  'buy', 'sell', 'order', 'position', 'portfolio', 'trading',
  'memory/', 'database', 'intent detection', 'detectIntent', 'buildContext',
  'localStorage.setItem', 'indexedDB'
];
const files = [];
function walk(dir) {
  try {
    for (const name of readdirSync(dir)) {
      const p = join(dir, name);
      const st = statSync(p);
      if (st.isDirectory()) walk(p);
      else if (/\.(ts|tsx)$/.test(name)) files.push(p);
    }
  } catch {}
}
roots.forEach(walk);
const violations = [];
for (const file of files) {
  const text = readFileSync(file, 'utf8');
  for (const token of forbidden) {
    if (text.includes(token)) violations.push(`${file}: ${token}`);
  }
}
if (violations.length) {
  console.error(violations.join('\n'));
  process.exit(1);
}
