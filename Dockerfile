FROM python:3.12-slim
WORKDIR /ramp
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 18469
CMD ["flask","--app","app.main:create_app","run","--host=0.0.0.0","--port=18469"]
