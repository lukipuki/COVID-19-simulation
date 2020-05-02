# Docker for running the C++ simulation
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf \
    && apt-get update \
    && apt-get install zsh git cmake ninja-build g++ \
    && apt-get install python3-pip python3-plotly python3-pandas

RUN rm -rf /tmp/* /var/lib/apt/lists/* /root/.cache/*

RUN pip3 install conan

RUN mkdir /covid19
