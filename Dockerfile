FROM python:3.8-slim

WORKDIR /workspace

COPY . .

CMD ["bin/book-analyzer.sh", "200", "<", "/workspace/test_data/bid_test00.in"]