FROM python:3.12-slim
LABEL maintainer="u123@ua.fm"

ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip && apt-get update && \
    apt-get install -y postgresql-client tzdata && rm -rf /var/lib/apt/lists/*

WORKDIR app/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

#ENTRYPOINT ["scrapy"]
#
#CMD ["crawl", "usedcars"]

CMD ["tail", "-f", "/dev/null"]
