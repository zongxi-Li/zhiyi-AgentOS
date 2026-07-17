FROM node:24-alpine AS build

WORKDIR /app

# 复制package文件并安装依赖
COPY package*.json ./
RUN npm ci

# 复制源代码并构建
COPY . .
RUN npm run build:docker

# 运行阶段
FROM nginx:alpine

RUN addgroup -g 10003 -S kinlin \
    && adduser -S -D -H -u 10003 -G kinlin kinlin \
    && chown -R 10003:10003 /usr/share/nginx/html /var/cache/nginx /etc/nginx/conf.d

# 复制构建结果
COPY --from=build /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx-main.conf /etc/nginx/nginx.conf

EXPOSE 8080

USER 10003:10003

CMD ["nginx", "-g", "daemon off;"]

