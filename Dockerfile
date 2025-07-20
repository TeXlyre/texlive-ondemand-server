FROM ubuntu:22.04

# Install base packages and TeX Live
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -q -y \
    wget \
    texlive-full \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libkpathsea-dev \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Build the C extensions
RUN python3 kpathsea_xetex_setup.py build_ext --inplace
RUN python3 kpathsea_pdftex_setup.py build_ext --inplace

# Install available font packages (non-critical)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -q -y \
    fonts-liberation \
    fonts-dejavu \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    fonts-droid-fallback \
    fonts-noto \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-ubuntu \
    fonts-lmodern \
    fonts-texgyre \
    && fc-cache -fv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* || true

# Install additional CTAN packages via tlmgr (if available)
RUN tlmgr update --self || true && \
    tlmgr install zref-clever || true && \
    tlmgr install collection-latexextra || true && \
    tlmgr install collection-fontsextra || true && \
    tlmgr install collection-mathscience || true && \
    mktexlsr || true

CMD ["python3", "wsgi.py"]