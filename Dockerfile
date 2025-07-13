# Dockerfile for PatentBot
FROM python:3.11-slim

# Set environment variables to avoid Python buffering issues
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY . .

# Create runtime directories for volume persistence
RUN mkdir -p app/chroma_db_patents app/parsed_patents

# Expose FastAPI port
EXPOSE 8000

# Set default command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
