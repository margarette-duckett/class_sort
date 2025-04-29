# Use the official Python image as the base image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy the requirements.txt into the container
COPY ./requirements.txt /app/requirements.txt

# Install the backend dependencies (FastAPI, Uvicorn, etc.)
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the backend app code into the container
COPY ./ /app/

# Expose the port that FastAPI will run on
EXPOSE 8000

# Start the FastAPI app with Uvicorn (app is in backend.py)
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]

