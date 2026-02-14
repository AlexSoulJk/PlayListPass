# Используем LTS версию Node.js (Iron) на базе Alpine Linux
FROM node:22-alpine

WORKDIR /app


COPY frontend/package.json ./

RUN npm install

COPY frontend/ .


EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]