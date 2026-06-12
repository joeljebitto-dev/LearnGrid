# syntax=docker/dockerfile:1.7
FROM node:22-alpine AS build

ARG VITE_API_BASE_URL=/api
ARG VITE_SENTRY_DSN=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_SENTRY_DSN=${VITE_SENTRY_DSN}

WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY frontend/package.json ./frontend/package.json
RUN pnpm install --frozen-lockfile

COPY frontend ./frontend
RUN pnpm -C frontend build

FROM nginx:1.27-alpine AS runtime
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html
EXPOSE 8080
