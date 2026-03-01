FROM node:20-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html

EXPOSE 80 443
