# Build the React frontend
FROM node:20-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
COPY tsconfig.app.json tsconfig.json tsconfig.node.json postcss.config.js tailwind.config.js vite.config.ts .
COPY index.html ./
COPY src ./src
RUN npm ci
RUN npm run build

# Build the Python runtime image
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend /app/dist ./dist
EXPOSE 5000
ENV FLASK_HOST=0.0.0.0
ENV FLASK_DEBUG=false
CMD ["sh", "-c", "gunicorn -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:${PORT:-5000} app:app"]
