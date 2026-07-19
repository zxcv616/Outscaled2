FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY ./app /app/app
EXPOSE 8010
CMD ["uvicorn", "app.props.server:app", "--host", "0.0.0.0", "--port", "8010"]
