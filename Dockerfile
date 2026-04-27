FROM python:3.11-slim
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    g++ \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip GDAL==3.6.2

# Copy only dependency files first to maximise layer caching
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt

CMD ["python"]
