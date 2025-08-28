FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code (with better cache invalidation)
COPY src/ ./src/
COPY public/ ./public/
COPY tsconfig.json ./
COPY *.config.js ./

# Build the app with timestamp to force rebuild
# Set CI=false to treat ESLint warnings as warnings, not errors
RUN echo "Build timestamp: $(date)" > build-info.txt && CI=false npm run build

# Production stage
FROM nginx:alpine

# Copy built app to nginx
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]