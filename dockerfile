FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python --version
RUN pip --version

RUN pip install -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 500

# Run Flask app
CMD ["python", "app.py"]
