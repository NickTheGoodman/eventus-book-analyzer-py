FROM python:3.8-slim

WORKDIR /workspace

RUN apt update && \
    apt-get -y install bc

COPY . .

CMD ["/workspace/bin/test.sh"]
