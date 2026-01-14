FROM ubuntu:20.04
RUN   apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -q -y wget \
    unzip \
    texlive-full \
    python3 \
    python3-pip \
    build-essential \
    python3-dev \
    libffi-dev \
    libc-ares-dev
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
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r /app/requirements.txt && echo "0.5"
WORKDIR /app
CMD ["python3", "wsgi.py"]