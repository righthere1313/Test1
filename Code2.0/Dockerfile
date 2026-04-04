FROM python:3.11-slim

WORKDIR /app
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpoppler-cpp-dev \
    poppler-utils \
    pkg-config \
    default-libmysqlclient-dev \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 120

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
