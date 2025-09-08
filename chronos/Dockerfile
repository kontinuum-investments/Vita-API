FROM ubuntu

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y python3.12 python3-pip python3.12-venv libgl1 libglx-mesa0 libglib2.0-0 libsm6 libxrender1
RUN python3.12 -m venv .venv && .venv/bin/pip install --no-cache-dir -r requirements.txt

EXPOSE 8003
ENTRYPOINT [".venv/bin/fastapi", "run", "--port", "8003"]