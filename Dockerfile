# Use the latest official Python image as a base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    netcat-openbsd \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with performance improvements
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the project files to the working directory
COPY . /app/

# Copy the wait script and make it executable
COPY wait-for-postgres.sh /wait-for-postgres.sh
RUN chmod +x /wait-for-postgres.sh

# Collect static files
RUN python manage.py collectstatic --no-input

# Expose the port your Django app runs on
EXPOSE 8000

# Use ENTRYPOINT and CMD separately for better containerization practices
ENTRYPOINT ["/bin/sh"]
CMD ["/wait-for-postgres.sh"]