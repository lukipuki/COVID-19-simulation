FROM docker.io/library/ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf
RUN apt update \
    && apt install -y python3-pip python3-numpy python3-pandas python3-flask python3-click \
    && apt install -y python3-xarray python3-requests \
    && rm -rf /tmp/* /var/lib/apt/lists/* /root/.cache/*

RUN pip3 install uwsgi
COPY . /python
RUN pip3 install /python/covid_graphs /python/covid_web && rm -rf /python
COPY covid_web/flask_server.sh /usr/bin/
ENTRYPOINT ["flask_server.sh"]
