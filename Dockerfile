FROM python:3.14.6
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH /app/src
CMD ["python", "src/__main__.py"]
