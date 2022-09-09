FROM python:3.10.7-alpine3.16

WORKDIR /usr/bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src .

CMD [ "python", "./main.py" ]
