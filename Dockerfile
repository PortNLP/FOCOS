# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Clone the GitHub repository
RUN apt-get update && apt-get install -y git
RUN apt-get install -y cron

# Install cron
RUN apt-get update

COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the migrations (adjust the commands based on your actual Flask application structure)
ENTRYPOINT tail -f /dev/null