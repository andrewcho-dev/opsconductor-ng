FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Install serve for production
RUN npm install -g serve

# Copy source code
COPY src/ ./src/
COPY public/ ./public/
COPY tsconfig.json ./
COPY *.config.js ./ 2>/dev/null || true

# Build the production bundle
RUN npm run build

EXPOSE 8000

ENV PORT=8000

# Serve the production build
CMD ["serve", "-s", "build", "-l", "8000"]