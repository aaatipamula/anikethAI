FROM python:3

WORKDIR /home/bot/ 

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN --mount=type=bind,source=./src/data,target=./src/data

CMD [ "python3", "./src/main.py" ]
