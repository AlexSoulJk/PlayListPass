# Фиксируем конкретную версию (Stable)
FROM nginx:1.25.4


RUN apt-get update && apt-get install -y mc && rm -rf /var/lib/apt/lists/*

RUN usermod -u 1000 nginx && groupmod -g 1000 nginx

COPY docker/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf