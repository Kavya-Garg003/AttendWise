# Use official Python image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Run Flask application
CMD ["python", "app.py"]
