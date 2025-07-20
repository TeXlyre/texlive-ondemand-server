FROM ubuntu:22.04

# Install base packages and TeX Live
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -q -y \
    wget \
    curl \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -q -y \
    texlive-full \
    python3.8 \
    python3.8-dev \
    python3.8-distutils \
    fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.8 using legacy installer
RUN curl https://bootstrap.pypa.io/pip/3.8/get-pip.py -o get-pip.py && \
    python3.8 get-pip.py && \
    rm get-pip.py

# Set Python 3.8 as default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

# Copy application files
COPY . /app
WORKDIR /app

# Install Python dependencies ignoring system packages
RUN python3.8 -m pip install --ignore-installed --break-system-packages -r requirements.txt

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

# Note: Using original format files and pre-compiled .so files
# No need to rebuild C extensions since we're using Python 3.8

CMD ["python3", "wsgi.py"]