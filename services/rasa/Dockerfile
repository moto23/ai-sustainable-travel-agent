# Use a specific Python version as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
# ✅ ADDED --timeout=600 to make the command more patient
RUN pip install --no-cache-dir --timeout=600 -r requirements.txt

# Download the SpaCy model
RUN python -m spacy download en_core_web_md

# Copy all the Rasa project files into the container
COPY . .

# Expose the port Rasa runs on
EXPOSE 5005

# The command to run when the container starts
CMD ["rasa", "run", "--enable-api", "--cors", "*", "--endpoints", "endpoints.yml"]