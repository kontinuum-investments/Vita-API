FROM python:3.11
COPY . .
WORKDIR .
RUN chmod +x /startup.sh
ENTRYPOINT ["/startup.sh"]