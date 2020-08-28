# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Base image for all other images.

FROM ubuntu:16.04
MAINTAINER ttrippel@google.com
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get upgrade -y && apt-get autoremove -y

# Setup directory structure
ENV SCRIPTS=/scripts
ENV SRC=/src
ENV PATH="$PATH:/scripts"
RUN mkdir -p $SCRIPTS $SRC && chmod a+rwx $SCRIPTS $SRC

# Install GCC, standard C library, make, perl, and python3
RUN apt-get install -y \
    curl \
    libc6-dev \
    binutils \
    libgcc-5-dev \
    g++ \
    perl \
    make \
    libfl-dev \
    zlibc \
    zlib1g \
    zlib1g-dev

# Install python3.8
RUN apt-get install -y software-properties-common && \
      add-apt-repository -y ppa:deadsnakes/ppa && \
      apt-get update
RUN apt-get install -y \
      python3.8 \
      python3.8-dev \
      python3.8-distutils
RUN rm /usr/bin/python3 && ln -s /usr/bin/python3.8 /usr/bin/python3

# Install pip
RUN curl https://bootstrap.pypa.io/get-pip.py -o $SRC/get-pip.py
RUN python3 $SRC/get-pip.py && \
      python3 -m pip install --upgrade pip && \
      rm $SRC/get-pip.py
