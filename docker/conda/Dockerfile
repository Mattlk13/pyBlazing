ARG  CUDA_VERSION=9.2
ARG  UBUNTU_VERSION=16.04
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION}

RUN apt-get update && \
    apt-get install -y git gcc make curl wget && \
    wget -q -O /tmp/miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash /tmp/miniconda.sh -b -f -p /usr/local/ && \
    rm -f /tmp/miniconda.sh && \
    conda update -y conda && \
    conda install -y conda-build anaconda-client cmake && \
    apt-get clean && \
    conda clean --all
