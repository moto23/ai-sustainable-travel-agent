# Use a specific Python version as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
# ✅ ADDED --timeout=600 to make the command more patient
RUN pip install --no-cache-dir --timeout=600 -r requirements.txt

# Copy your application code
COPY . .

# Command to run your RAG system (change 'main.py' to your actual script name)
CMD ["python", "main.py"]