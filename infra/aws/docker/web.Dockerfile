# infra/aws/docker/web.Dockerfile
# Image web (T095): build Vite bang npm ci + npm run build (typecheck nhu CI), phuc vu ban tinh bang nginx khong
# chay root; /api/ chuyen toi inference-api trong mang Compose. Build tu goc repo:
# docker build -f infra/aws/docker/web.Dockerfile .
ARG NODE_IMAGE=node:24.18.0-alpine
ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:1.30-alpine

FROM ${NODE_IMAGE} AS build
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund
COPY apps/web/ ./
RUN npm run build

FROM ${NGINX_IMAGE} AS runtime
COPY infra/aws/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY infra/aws/nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"]
