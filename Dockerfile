FROM python:3.12-slim

# System libraries GeoDjango needs (GDAL/GEOS/PROJ) - not a normal Python
# dependency, so a generic buildpack (Railway's Railpack, Nixpacks, etc.)
# won't install these automatically. libgdal-dev specifically provides the
# unversioned `libgdal.so` symlink that Django's ctypes-based GDAL lookup
# requires (the bare `gdal-bin` runtime package alone isn't enough).
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
