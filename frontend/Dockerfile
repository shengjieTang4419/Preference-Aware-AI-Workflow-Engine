FROM node:20-alpine

WORKDIR /app

# 依赖
COPY package.json package-lock.json* ./
RUN npm install

# 源码
COPY . .

EXPOSE 5173

CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "5173"]
