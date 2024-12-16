# Stage 1: Build Frontend
FROM node:19 AS frontend-builder

# Set working directory
WORKDIR /app/frontend

# Copy frontend code
COPY ./frontend/package*.json ./
COPY ./frontend/ ./
WORKDIR /app/frontend/app
# Install dependencies and build the frontend
RUN npm install
RUN npm run build

# Stage 2: Build Backend
FROM python:3.10-slim AS backend-builder

# Set working directory
WORKDIR /app/backend

# Copy backend code
COPY ./backend/ ./

# Create and activate virtual environment
RUN python -m venv /venv

# Install dependencies
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 3: Production Image
FROM python:3.10-slim AS final

# Install nginx for serving the frontend
RUN apt-get update && apt-get install -y nginx && apt-get clean

# Copy backend and frontend from previous stages
WORKDIR /app
COPY --from=backend-builder /app/backend /app/backend
COPY --from=backend-builder /venv /venv
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Set up nginx configuration
RUN rm /etc/nginx/sites-enabled/default
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# Expose ports
EXPOSE 8090 80

# Start both backend and nginx
CMD ["sh", "-c", "nginx && /venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8090"]