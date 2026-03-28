FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    APP_MODE=streamlit \
    PORT=8501

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8501 8000

CMD ["sh", "-c", "if [ \"$APP_MODE\" = \"api\" ]; then uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}; else streamlit run app.py --server.port ${PORT:-8501}; fi"]
