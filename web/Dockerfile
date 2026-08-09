ARG NODE_IMAGE=node:24.14.0-bookworm-slim@sha256:d8e448a56fc63242f70026718378bd4b00f8c82e78d20eefb199224a4d8e33d8

FROM ${NODE_IMAGE} AS build

ENV CI=1 \
    NODE_ENV=production \
    PNPM_HOME=/pnpm \
    PATH=/pnpm:${PATH}

WORKDIR /app

RUN corepack enable \
    && corepack prepare pnpm@11.9.0 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm run lint \
    && pnpm run build \
    && node --test tests/rendered-html.test.mjs

FROM ${NODE_IMAGE} AS runtime

ARG VCS_REF=unknown

LABEL org.opencontainers.image.title="shuheng-research-web" \
      org.opencontainers.image.description="枢衡只读研究展示站" \
      org.opencontainers.image.revision="${VCS_REF}"

ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000 \
    TZ=Asia/Shanghai

WORKDIR /app

COPY --from=build --chown=node:node /app/dist ./dist
COPY --from=build --chown=node:node /app/node_modules/vinext/dist ./vinext/dist
COPY --from=build --chown=node:node /app/node_modules/vinext/package.json ./vinext/package.json
COPY --chown=node:node docker/server.mjs ./server.mjs

USER node

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]

CMD ["node", "server.mjs"]
