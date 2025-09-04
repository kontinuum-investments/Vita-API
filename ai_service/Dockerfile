FROM python:3.12

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y libgl1
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8002
ENTRYPOINT ["fastapi", "run", "--port", "8002"]