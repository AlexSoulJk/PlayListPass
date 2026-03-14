# Frontend документация

## Текущий стек
- React `19.2.0`
- React DOM `19.2.0`
- TypeScript `5.9.x`
- Vite `7.3.x`
- `@vitejs/plugin-react` `5.1.x`
- ESLint `9.x` + `typescript-eslint` + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`

## Текущая структура и состояние
- Точка входа: `src/main.tsx`
- Корневой компонент: `src/App.tsx`
- Стили: `src/index.css` и `src/App.css`
- UI сейчас шаблонный (стартовый Vite + React счетчик), без интеграции с backend API.

## Конфигурация разработки
- Скрипты:
  - `npm run dev` — dev-сервер Vite
  - `npm run build` — сборка (`tsc -b && vite build`)
  - `npm run lint` — линтер
  - `npm run preview` — предпросмотр production-сборки
- TypeScript в строгом режиме (`strict: true`), `moduleResolution: bundler`.

## Что сейчас не подключено
- В текущем `package.json` нет библиотек роутинга (например, `react-router-dom`), state-менеджмента (Redux/Zustand) и UI-кита (например, Mantine).
