# FROM python:3.9-alpine

FROM xserrat/facebook-demucs:latest

WORKDIR /app

RUN pip3 install requests minio redis ffmpeg

COPY worker.py /app

ENV PYTHONUNBUFFERED=1
# CMD [ "python3", "worker.py"]
ENTRYPOINT ["python3", "worker.py"]
