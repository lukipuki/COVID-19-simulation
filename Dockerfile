FROM ubuntu:19.10

ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf \
    && apt-get update \
    && apt-get install zsh git cmake ninja-build g++ libgtest-dev libgmock-dev \
    && apt-get install python3-pip python3-plotly python3-pandas libprotobuf-dev protobuf-compiler

RUN rm -rf /tmp/* /var/lib/apt/lists/* /root/.cache/*

RUN pip3 install conan

RUN mkdir /covid19
