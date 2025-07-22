FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY hermes_server.py .
COPY hermes.html .
COPY history.html .
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

# Expose port 8590
EXPOSE 8590

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8590

# Run the server using the startup script
CMD ["./start.sh"]