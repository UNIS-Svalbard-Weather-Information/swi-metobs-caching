# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libexpat1 \
    libgdal-dev \
    gdal-bin \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the specified directories and files into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy the entry point script
COPY entrypoint.sh /app/entrypoint.sh

# Make the entry point script executable
RUN chmod +x /app/entrypoint.sh

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Use the entry point script as the container's entry point
ENTRYPOINT ["/app/entrypoint.sh"]
