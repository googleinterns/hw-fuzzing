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

# Base image for building/simulating OpenTitan design.

FROM ubuntu:16.04
MAINTAINER ttrippel@google.com
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get upgrade -y && apt-get autoremove -y

ENV TOOLS=/tools
ENV SRC=/src

RUN mkdir -p $TOOLS $SRC && chmod a+rwx $TOOLS $SRC

# Putting installation steps in a script reduces the number of intermediate
# layers generated from the Dockerfile.
COPY checkout_build_install_otsw.sh /root/
RUN /root/checkout_build_install_otsw.sh
RUN rm /root/checkout_build_install_otsw.sh
