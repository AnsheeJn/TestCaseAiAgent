# Use a Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libexpat1 \
    libx11-6 \
    libxcursor1 \
    libxrandr2 \
    libxscrnsaver1 \
    libgtk-3-0 \
    libgconf-2-4 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy your requirements.txt and install Python dependencies
COPY ai-test-agent/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's code
COPY ai-test-agent/ ./

# Install the Playwright browser binaries
RUN playwright install chromium

# Expose the port Streamlit runs on
EXPOSE 8501

# Run the Streamlit app
ENTRYPOINT ["streamlit", "run", "app.py"]
