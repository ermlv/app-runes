// Деплой бота в репозиторий github.com/ermlv/runediviner (пуш = авто-деплой
// на bothost.ru). Шаги: экспорт текстов рун → копия bot/ → commit → push.
// Запуск: npm run deploy:bot. Путь к локальному клону: DEPLOY_REPO_PATH
// (по умолчанию ../runediviner относительно корня репозитория).
import { spawnSync } from 'node:child_process';
import { cpSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const deployPath = path.resolve(repoRoot, process.env.DEPLOY_REPO_PATH || '../runediviner');
// Секреты, окружение и тесты в деплой-репозиторий не попадают.
const EXCLUDE = new Set(['.env', '.venv', 'data', '__pycache__', '.pytest_cache', 'tests']);

function die(msg) {
  console.error(`deploy:bot: ${msg}`);
  process.exit(1);
}

// 1) Тексты рун — всегда свежие.
const exported = spawnSync(process.execPath,
  [path.join(repoRoot, 'scripts', 'export-runes.mjs')], { stdio: 'inherit' });
if (exported.status !== 0) die(`export:runes завершился с кодом ${exported.status}`);

// 2) Локальный клон репозитория деплоя.
if (!existsSync(deployPath)) {
  die(`нет каталога ${deployPath} — клонируйте: git clone git@github.com:ermlv/runediviner.git ${deployPath}`);
}
const remote = spawnSync('git', ['-C', deployPath, 'remote', 'get-url', 'origin'],
  { encoding: 'utf8' });
if (remote.status !== 0) die(`${deployPath} не является git-репозиторием с remote origin`);

// 3) Копия содержимого bot/ (bot.py должен лежать в корне — требование bothost).
cpSync(path.join(repoRoot, 'bot'), deployPath, {
  recursive: true,
  filter: (src) => !EXCLUDE.has(path.basename(src)),
});

// 4) Коммит и пуш (пуш = авто-деплой на bothost).
const git = (args) => spawnSync('git', ['-C', deployPath, ...args], { stdio: 'inherit' });
git(['add', '-A']);
const staged = spawnSync('git', ['-C', deployPath, 'diff', '--cached', '--quiet']);
if (staged.status !== 0) {
  const stamp = new Date().toISOString().replace('T', ' ').slice(0, 19);
  const commit = spawnSync('git', [
    '-C', deployPath,
    '-c', 'user.name=qwen.ai[bot]',
    '-c', 'user.email=qwenlm-intl@service.alibaba.com',
    'commit', '-m', `deploy: ${stamp} UTC`,
  ], { stdio: 'inherit' });
  if (commit.status !== 0) die(`git commit завершился с кодом ${commit.status}`);
} else {
  console.log('deploy:bot: изменений нет, коммит не нужен');
}
const push = git(['push', '-u', 'origin', 'main']);
if (push.status !== 0) die(`git push завершился с кодом ${push.status}`);
console.log(`deploy:bot: запушено в ${deployPath} → origin/main`);
