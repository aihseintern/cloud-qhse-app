FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 libgl1 libpq-dev musl-dev -y 

RUN pip install --no-cache-dir -r docker-requirements.txt

EXPOSE 5000

ENV FLASK_APP=app/__init__.py

CMD ["flask", "run", "--host=10.184.0.32"]
