FROM ubuntu:latest
COPY . .
WORKDIR .
RUN chmod +x initialize.sh && ./initialize.sh

ENTRYPOINT uvicorn main:app --host 0.0.0.0 --port 443