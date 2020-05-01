FROM ubuntu:19.10

ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf
RUN apt update \
    && apt install -y python3-pip python3-numpy python3-pandas \
    && rm -rf /tmp/* /var/lib/apt/lists/* /root/.cache/*

COPY covid_graphs /covid19_graphs
RUN pip3 install /covid19_graphs && rm -rf /covid19_graphs

COPY web /covid19_web
RUN pip3 install /covid19_web && rm -rf /covid19_web
