# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# ffmpeg is required for MoviePy and Whisper
# git is required for installing some python packages if needed
# build-essential is for compiling some python extensions
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# We use --no-cache-dir to keep the image small
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download a small Whisper model to speed up first run (optional but recommended)
# This avoids downloading the model every time the container starts
RUN python -c "import whisper; whisper.load_model('base')"

# Copy the rest of the application code
COPY . .

# Create a directory for temporary files
RUN mkdir -p temp && chmod 777 temp

# Expose the port Streamlit runs on
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Define the command to run the application
CMD ["streamlit", "run", "app.py"]
