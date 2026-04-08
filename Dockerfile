FROM python:3.11-slim

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- THE SPEED TRICK ---
# Copy ONLY requirements first
COPY requirements.txt .

# Install dependencies. Railway will CACHE this layer. 
# As long as requirements.txt doesn't change, this step takes 0 seconds in future builds!
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code LAST
COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]