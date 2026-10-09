# ========================================================
# Stage 1: Build React Vite App
# ========================================================
FROM node:20-alpine AS build

WORKDIR /app

# Copy package.json và cài đặt dependencies
COPY package*.json ./
RUN npm ci

# Copy mã nguồn và build static files
COPY . .
RUN npm run build

# ========================================================
# Stage 2: Serve với Nginx siêu nhẹ (~25MB)
# ========================================================
FROM nginx:alpine

# Copy bản build từ stage 1 vào thư mục public của Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copy cấu hình reverse proxy Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
