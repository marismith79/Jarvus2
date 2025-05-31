FROM --platform=linux/amd64 dorowu/ubuntu-desktop-lxde-vnc:focal

# Install Python and pip
USER root
RUN rm -f /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y python3 python3-pip wget firefox \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz \
    && tar -xvzf geckodriver-v0.33.0-linux64.tar.gz \
    && chmod +x geckodriver \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.33.0-linux64.tar.gz

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir websockify

# Copy application code
COPY . .

# Copy supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports
EXPOSE 8000 6080 5900

# Create supervisor config for FastAPI
RUN echo '[program:fastapi]\n\
command=python3 -m uvicorn app:app --host 0.0.0.0 --port 8000\n\
directory=/app\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/fastapi.err.log\n\
stdout_logfile=/var/log/fastapi.out.log\n\
' > /etc/supervisor/conf.d/fastapi.conf

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set ENV DISPLAY=:99
ENV DISPLAY=:99
RUN apt-get update && apt-get install -y libpci3 libdbus-glib-1-2 && rm -rf /var/lib/apt/lists/*

# The base image already has a startup script that runs supervisord
CMD ["/startup.sh"] 