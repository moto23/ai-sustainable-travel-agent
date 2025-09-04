# Use a specific Python version as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements and install
# Make sure you have a requirements.txt in your apis folder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Command to run your FastAPI app (make sure main.py and app are your actual filenames)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]