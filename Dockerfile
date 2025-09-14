FROM python:slim

# Install Git and other dependencies
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Copy the current directory to /swi
COPY . /swi/

# Set the working directory
WORKDIR /swi

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make run.sh executable
RUN chmod +x /swi/run.sh

# Use run.sh as the entry point
ENTRYPOINT ["/swi/run.sh"]

