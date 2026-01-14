FROM ubuntu:20.04
RUN   apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -q -y wget \
    unzip \
    ca-certificates \
    software-properties-common \
    texlive-full \
    && rm -rf /var/lib/apt/lists/*
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -q -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/*
RUN wget -q https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py && \
    python3.11 /tmp/get-pip.py && \
    rm -f /tmp/get-pip.py
COPY . /app

#### Debug block - This is a verbose approach for adding a package, but just to see if it works ####
RUN cd /tmp && \
    wget https://ctan.org/tex-archive/macros/latex/contrib/zref-clever.zip && \
    unzip zref-clever.zip && \
    cd zref-clever && \
    tex zref-clever.ins && \
    mkdir -p /usr/share/texlive/texmf-dist/tex/latex/zref-clever && \
    cp zref-clever.sty /usr/share/texlive/texmf-dist/tex/latex/zref-clever/ && \
    mktexlsr && \
    rm -rf /tmp/zref-clever*
####################################################################################################
RUN python3.11 -m pip install --upgrade pip && \
    python3.11 -m pip install -r /app/requirements.txt && echo "0.5"
WORKDIR /app
CMD ["python3.11", "wsgi.py"]