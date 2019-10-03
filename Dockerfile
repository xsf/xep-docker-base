# Base docker image for building XEPs
# Sets up directories and dependencies
# docker build . -t xmppxsf/xeps-base -f Dockerfile.base

FROM debian:8
MAINTAINER XSF Editors <editor@xmpp.org>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        xsltproc libxml2-utils libxml2 texlive fonts-inconsolata make nginx \
        curl python python-pip texlive-xetex texlive-fonts-recommended \
        texlive-fonts-extra lmodern python3 && \
    rm -rf /var/lib/apt/lists/*

COPY texml-2.0.2 /src/texml-2.0.2

RUN pip install /src/texml-2.0.2 && rm -rf /src/texml-2.0.2

RUN mkdir -p /src/resources /var/www/html/extensions
