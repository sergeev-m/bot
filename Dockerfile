FROM python:3.11-alpine3.18

RUN mkdir /app
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
CMD [ "python", "bot.py" ]
