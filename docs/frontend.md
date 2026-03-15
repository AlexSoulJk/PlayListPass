# Документация Frontend

## Текущий стек
- React `19.2.0`
- React DOM `19.2.0`
- TypeScript `5.9.x`
- Vite `7.3.x`
- React Router DOM `6.30.x`
- React Hook Form `7.54.x`
- Zod `3.24.x`
- Axios `1.7.x`
- Vitest `4.x` + Testing Library + jsdom

## Структура
- Точка входа: `src/main.tsx`
- Корневой компонент: `src/App.tsx`
- Роутинг: `src/app/router`
- Auth-провайдер и контекст: `src/app/providers`
- UI auth-фичи: `src/features/auth/ui`
- HTTP-клиент: `src/shared/api/httpClient.ts`
- Тесты: `frontend/tests`

## Скрипты
- `npm run dev` — запуск dev-сервера Vite
- `npm run build` — production-сборка (`tsc -b && vite build`)
- `npm run test` — запуск тестов в watch-режиме
- `npm run test:run` — одноразовый прогон тестов
- `npm run lint` — запуск ESLint
- `npm run preview` — предпросмотр production-сборки

## Конфигурация API
- Базовый URL задается через `VITE_API_URL`.
- Если переменная не задана, используется `http://localhost:8000`.
