FROM ubuntu

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y python3.12 python3-pip python3.12-venv
RUN python3.12 -m venv .venv && .venv/bin/pip install --no-cache-dir -r requirements.txt

EXPOSE 8001
ENTRYPOINT ["sh", "-c", ".venv/bin/mcpo --api-key \"$API_KEY\" --port 8001 -- .venv/bin/python main.py"]