# Uses lightweight Python 3.12 image as the base OS
FROM python:3.12-slim

# Sets the working directory inside the container
WORKDIR /app

# Copies and installs Python dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copies the application source code into the container
COPY src/ ./src/