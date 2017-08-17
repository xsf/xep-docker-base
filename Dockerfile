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
        texlive-fonts-extra lmodern && \
    rm -rf /var/lib/apt/lists/*
RUN curl https://pilotfiber.dl.sourceforge.net/project/getfo/texml/texml-2.0.2/texml-2.0.2.tar.gz -o texml-2.0.2.tar.gz && \
    tar -xf texml-2.0.2.tar.gz && \
    pip install texml-2.0.2/ && \
    rm -rf texml-2.0.2

RUN mkdir -p /src/resources /var/www/html/extensions
