# Use a Python base image
FROM python:3.9-slim

# Set environment variables for Elasticsearch
ENV ELASTICSEARCH_HOST=""
ENV ELASTICSEARCH_USERNAME=""
ENV ELASTICSEARCH_PASSWORD=""

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt and .env files into the container
COPY requirements.txt ./
COPY src/.env ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY src/main.py ./

# Define a volume mount point
VOLUME /var/log/openvpn

# Run the Python script when the container launches
CMD [ "python", "./main.py", "--status-file", "/var/log/openvpn/openvpn-status.log" ]
