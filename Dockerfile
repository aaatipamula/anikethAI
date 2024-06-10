# syntax = docker/dockerfile:experimental
FROM python:3

WORKDIR /home/bot/ 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY . .

CMD [ "python3", "./src/main.py" ]
