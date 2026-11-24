// Выгружает данные рун из src/data/runes.ts в bot/runes.json.
// Node 22 читает .ts файлы нативно (type stripping) — новых зависимостей не нужно.
// Запуск: npm run export:runes
import { writeFileSync } from 'node:fs';
import { runes } from '../src/data/runes.ts';

const out = new URL('../bot/runes.json', import.meta.url);
writeFileSync(out, JSON.stringify(runes, null, 2) + '\n');
console.log(`runes.json: ${runes.length} рун`);
