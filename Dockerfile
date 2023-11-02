FROM python:3.11
WORKDIR /usr/src/app
RUN apt update
RUN pip install --upgrade pip


RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev
RUN pip install GDAL==3.6.2


# Copy only necessary files
COPY requirements.txt .
COPY requirements-dev.txt .
COPY bootstrap.sh /bootstrap.sh
# Set executable permissions, install Python dependencies
RUN chmod +x /bootstrap.sh && \
    pip install -r requirements-dev.txt && \
    pip install -r requirements.txt

# Set the entrypoint
ENTRYPOINT ["/bootstrap.sh"]
