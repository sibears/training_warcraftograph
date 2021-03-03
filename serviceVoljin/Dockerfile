FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./
RUN apk update && \
	apk add --virtual build-deps build-base libffi-dev python3-dev jpeg-dev zlib-dev && \
	apk add libjpeg && \
	LIBRARY_PATH=/lib:/usr/lib pip install --no-cache-dir -r requirements.txt && \
	apk del build-deps && \
	rm -rf /var/cache/apk/*

COPY ./ ./

EXPOSE 8084
VOLUME ["/app/db_secrets.db", "/app/cache"]

CMD ["python3", "main.py"]
