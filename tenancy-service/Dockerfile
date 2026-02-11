FROM node:22-slim

WORKDIR /app

# Enable pnpm via corepack
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy dependency files first for layer caching
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source and config
COPY src/ src/
COPY drizzle/ drizzle/
COPY drizzle.config.ts tsconfig.json tsconfig.build.json nest-cli.json ./

# Build the NestJS application
RUN pnpm build

EXPOSE 5001

CMD ["node", "dist/main"]
