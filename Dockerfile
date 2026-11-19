# Optional container route (Railway / Fly.io / local Docker).
# server.py reads $PORT, so any host-assigned port works.
FROM python:3.12-slim
WORKDIR /app
COPY guard.py server.py ./
EXPOSE 8080
CMD ["python3", "server.py"]
