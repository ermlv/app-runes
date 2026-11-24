# AGENTS.md

Rune divination SPA (Russian UI) — React 18 + TypeScript + Vite 6 + Tailwind 4, wrapped for Android via Capacitor 8. No test suite exists.

## Commands

- `npm run dev` — dev server on `0.0.0.0:3000` (strictPort, HMR on same port)
- `npm run build` — web build → `dist/`
- `npm run typecheck` — `tsc --noEmit` (needs `"types": ["vite/client"]` in `tsconfig.json` for `import.meta.env`)
- APK: `npm run build` → `npx cap sync android` → `cd android && ./gradlew assembleDebug` → `android/app/build/outputs/apk/debug/app-debug.apk`

Order matters: `dist/` is gitignored but is `webDir` for Capacitor — always build before `cap sync`. After changing `resources/icon.png` or `resources/splash.png`, run `npx @capacitor/assets generate --android` (writes into `android/app/src/main/res/`).

## Architecture

- All app logic/UI is `src/App.tsx` (single component: intro → draw 3 runes → result). Rune content lives in `src/data/runes.ts` (24 Elder Futhark runes, per-position texts, optional reversed variants; 30% reversed chance is hardcoded in `getRandomRune`).
- `package.json` carries many unused sandbox leftovers (`@supabase/*`, `recharts`, `react-router-dom`, `@dnd-kit/*`, `framer-motion`, `lucide-react`, `uuid`, `date-fns`, `canvas-confetti`). `src/` imports only `react`/`react-dom`. Do not assume these libraries are wired in.
- PWA: `public/manifest.webmanifest`, `public/sw.js`, `public/icons/*`. Service worker registers only outside Capacitor (`!("Capacitor" in window)` guard in `src/main.tsx`) — keep that guard.
- `src/index.css`: self-hosted `@font-face` (Noto Sans Runic, `public/fonts/noto-sans-runic.woff2`) must stay **after** `@import "tailwindcss"` — a `@font-face` before `@import` silently breaks Tailwind.

## Android project

- Capacitor config: `capacitor.config.ts` (`appId: com.runes.divination`, `webDir: dist`). Native tree is `android/` (committed).
- SDK 36: `compileSdk/targetSdk 36`, `minSdk 24`, AGP 8.13.0.
- Release signing: keystore at `/home/coder/.android/runes-release.keystore` (alias `runes`), credentials in `android/keystore.properties` (gitignored — do not commit). `buildTypes.release` picks it up automatically; ship `assembleRelease` output, not `assembleDebug` (debug is signed with `CN=Android Debug`).
- App icon master: `public/icons/icon-1024.png` (from Figma, "Obsidian Runes"). After replacing it, regenerate sizes in `public/icons/`, `resources/icon.png`, then `npx @capacitor/assets generate --android` and rebuild both targets.

## Telegram-бот (`bot/`)

Дублёр расклада «Три Норны» в Telegram (@runediviner_bot): Python 3.11+ / aiogram 3 / SQLite, структура — как в penjoy-bot (`/home/coder/mar-penjoy/penjoy-bot`). Дизайн: `docs/superpowers/specs/2026-11-24-rune-bot-design.md`.

- `npm run export:runes` — перегенерировать `bot/runes.json` после правок `src/data/runes.ts` (файл генерируется, руками не править).
- `npm run deploy:bot` — экспорт текстов → копия `bot/` в `../runediviner` → commit/push в github.com/ermlv/runediviner; пуш в `main` = авто-деплой на bothost.ru.
- Тесты: `cd bot && .venv/bin/python -m pytest -q`. Локальный запуск: `cd bot && .venv/bin/python bot.py`.
- Токен — **только** в `bot/.env` (никогда не коммитить; в Git и планы не вписывать). На bothost `BOT_TOKEN` подставляет платформа.
- `bot/.venv` собран на uv-python: системный python3.12 на этой машине без модуля `sqlite3` — см. `bot/README.md`.

## Landing (`landing/`)

- Static landing page replicating the `ermlv.ru/app-rnd` template (no build step): `landing/index.html`.
- `landing/web/` is the built PWA — it must be served from a subdirectory, so the app uses relative paths (`base: './'` in `vite.config.js`, relative manifest/SW URLs). Do not switch back to absolute `/...` paths.
- Deploy bundle = `landing/` as-is; the green «Онлайн-версия» button links to `web/`, APK lives in `landing/downloads/`.
- After app changes: `npm run build` → copy `dist/*` → `landing/web/` → refresh APK in `landing/downloads/` and the size/version in `landing/index.html`.

## Environment gotchas (this machine)

- System JVMs under `/usr/lib/jvm` are JRE-only (no `javac`); Gradle fails with `does not provide the required capabilities: [JAVA_COMPILER]`. Fix is in place: `android/gradle.properties` pins `org.gradle.java.home=/home/coder/jdk/jdk-21.0.13+9` (Temurin JDK unpacked manually).
- Android SDK at `/home/coder/android-sdk` — `sdk.dir` in `android/local.properties`; export `ANDROID_HOME=$HOME/android-sdk` when running Gradle.
- Headless browser verification: `chromium --headless --screenshot` silently writes nothing; Playwright's bundled browsers fail (`GLIBCXX_3.4.29` missing, system has 3.4.28); chrome-devtools MCP expects `/opt/google/chrome`. Working path: `puppeteer-core` with `executablePath: '/usr/bin/chromium'`.
