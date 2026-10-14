FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home armor
COPY . .
RUN mkdir -p /app/instance && chown -R armor:armor /app
USER armor
EXPOSE 8080
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "--call", "techarmor:create_app"]
