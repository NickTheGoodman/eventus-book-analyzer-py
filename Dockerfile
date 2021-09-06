FROM python:3.8-slim

WORKDIR /workspace

COPY . .

CMD ["bin/book-analyzer.sh", "200"]