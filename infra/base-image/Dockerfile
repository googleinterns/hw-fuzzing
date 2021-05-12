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

FROM ubuntu:18.04
MAINTAINER trippel@umich.edu
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get upgrade -y && apt-get autoremove -y

# Setup directory structure
ENV SCRIPTS=/scripts
ENV SRC=/src
ENV PATH="$PATH:/scripts"
RUN mkdir -p $SCRIPTS $SRC && chmod a+rwx $SCRIPTS $SRC

# Install basic packages
RUN apt-get install -y \
    curl \
    binutils \
    g++ \
    perl \
    python3 \
    python3-pip \
    make \
    libfl-dev \
    zlibc \
    zlib1g \
    zlib1g-dev
