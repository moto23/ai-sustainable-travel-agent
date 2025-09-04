# Use a specific Python version as a base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# --- MULTI-STEP INSTALLATION FOR BETTER CACHING ---

# STEP 1: Copy ONLY the requirements file first
COPY requirements.txt .

# STEP 2: Install the largest libraries first to create a stable cache layer
# This is the step that takes a long time, but will only run once.
RUN pip install --no-cache-dir --timeout=600 torch transformers

# STEP 3: Install the rest of the smaller libraries
RUN pip install --no-cache-dir --timeout=600 -r requirements.txt

# STEP 4: Download the SpaCy model
RUN python -m spacy download en_core_web_md

# Copy all the action server files into the container
COPY . .

# Expose the port the action server runs on
EXPOSE 5055

# The command to run when the container starts
CMD ["rasa", "run", "actions"]