FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend.py server.py JinaEmbeddings.py ./
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
EXPOSE 10000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "10000"]
