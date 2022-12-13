FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    automake \
    libtool \
    flex \
    bison \
    pkg-config \
    libboost-all-dev \
    libevent-dev \
    libdouble-conversion-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    liblz4-dev \
    liblzma-dev \
    libsnappy-dev \
    zlib1g-dev \
    binutils-dev \
    libjemalloc-dev \
    libssl-dev

RUN wget http://archive.apache.org/dist/thrift/0.11.0/thrift-0.11.0.tar.gz && \
    tar xzf thrift-0.11.0.tar.gz && \
    rm thrift-0.11.0.tar.gz && \
    cd thrift-0.11.0 && \
    ./configure --without-python && \
    make && \
    make install

COPY . /app

WORKDIR /app

# Set the default target language to Python
ENV TARGET_LANG python

CMD thrift -r --gen $TARGET_LANG /app/$THRIFT_FILE
