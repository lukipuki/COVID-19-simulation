FROM ubuntu:19.10

ENV DEBIAN_FRONTEND=noninteractive
RUN echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf
RUN apt update \
    && apt install -y python3-pip python3-numpy python3-pandas \
    && rm -rf /tmp/* /var/lib/apt/lists/* /root/.cache/*

COPY python /python
RUN pip3 install /python/covid_graphs /python/covid_web && rm -rf /python
RUN pip3 install uwsgi
COPY python/covid_web/flask_server.sh /usr/bin/
ENTRYPOINT ["flask_server.sh"]
