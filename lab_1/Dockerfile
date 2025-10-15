FROM python:3.11-slim

WORKDIR /app

COPY server.py /app/
COPY client.py /app/

RUN mkdir -p /app/www /app/downloads

RUN chmod +x /app/server.py /app/client.py

EXPOSE 8000

CMD ["python", "server.py", "/app/www", "8000"]
