FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

EXPOSE 8001

# Start FastAPI with uvicorn (task consumer starts in background via lifespan)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
