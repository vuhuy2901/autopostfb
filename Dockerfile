# Sử dụng Python 3.11 slim Debian
FROM python:3.11-slim

# Ngăn Python tạo file .pyc và bật unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết, Google Chrome và Xvfb (Màn hình ảo GUI)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    curl \
    unzip \
    xvfb \
    x11-utils \
    libnss3 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Google Chrome Stable chính chủ
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng
COPY . .

# Tạo thư mục dữ liệu và phân quyền
RUN mkdir -p chrome_profile posts/sample_post/images logs data .temp_mutated_images

# Mở cổng 5000 cho Web Dashboard
EXPOSE 5000

# Script khởi động Xvfb và ứng dụng Web
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & export DISPLAY=:99 && python -u web_app.py"]
