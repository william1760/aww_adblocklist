FROM debian:stable

# Install Bash, Python3, pip, Chromium & dependencies
RUN apt-get update && apt-get install -y \
    bash \
    python3 \
    python3-pip \
    chromium \
    chromium-driver \
    wget \
    unzip \
    gnupg \
    curl \
    fonts-liberation \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxi6 \
    libxrender1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    xvfb \
    iputils-ping \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Environment variables so Selenium uses Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER=/usr/bin/chromedriver
ENV DISPLAY=:99

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN python3 -m pip config set global.break-system-packages true
RUN pip3 install --no-cache-dir -r requirements.txt

# Link the host current directory into /app/porn_scraper for easier editing
# (At runtime, use: docker run -v $(pwd):/app/porn_scraper ...)
RUN mkdir -p /app/porn_scraper

# Remove this COPY so we rely on volume mount instead of baking the script into the image
# COPY porn_scraper.py .

# Default to bash for debugging
ENTRYPOINT ["tail", "-f", "/dev/null"]