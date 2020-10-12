# Copyright 2020 Timothy Trippel
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

# Docker image for fuzzing various lock circuits with AFL
ARG FUZZER=sim
FROM hw-fuzzing/base-${FUZZER}
MAINTAINER trippel@umich.edu

# create DUT directory
ENV DUT=$HW/aes
RUN mkdir $DUT

# Copy in HDL and testbench
RUN apt-get install -y git
ENV OPENTITAN_ROOT=$HW/opentitan
RUN git clone --depth=1 https://github.com/lowRISC/opentitan.git $OPENTITAN_ROOT
RUN apt-get remove --purge -y git && apt-get autoremove -y
COPY hdl $DUT/hdl
COPY tb $DUT/tb
COPY seeds $DUT/seeds

# Copy in build scripts
COPY Makefile $DUT/

WORKDIR $DUT
CMD ["run"]
