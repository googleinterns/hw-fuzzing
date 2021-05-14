# Copyright 2021 Timothy Trippel
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

ARG FUZZER=sim
FROM hw-fuzzing/base-${FUZZER}
MAINTAINER trippel@umich.edu

# Test that TOPLEVEL argument was passed
ARG TOPLEVEL
RUN test -n "$TOPLEVEL"

# Create DUT directory
ENV DUT=$HW/$TOPLEVEL
RUN mkdir $DUT 

# Copy in HDL and testbench
RUN apt-get install -y git sed
ENV DUT_HDL_DIR=$HW/rfuzz
RUN git clone --branch hwfuzz-usenix21 \
      https://github.com/timothytrippel/rfuzz.git $DUT_HDL_DIR
ARG VERSION=HEAD
RUN cd $DUT_HDL_DIR && git checkout ${VERSION}
RUN cd $DUT_HDL_DIR && \
      sed -i 's/git@github.com:/https:\/\/github.com\//' .gitmodules && \
      git submodule update --init
ENV PATH="${PATH}:${DUT}/hdl_generator"
COPY $TOPLEVEL/tb $DUT/tb
COPY $TOPLEVEL/seeds $DUT/seeds

# Install RFUZZ circuit building dependencies
RUN apt-get install -y \
      meson \
      pkg-config \
      openjdk-8-jdk \
      cargo

# Install SBT
RUN echo "deb https://dl.bintray.com/sbt/debian /" | \
      tee -a /etc/apt/sources.list.d/sbt.list
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 \
      --recv 2EE0EA64E40A89B84B2DF73499E82A75642AC823
RUN apt-get update && apt-get install -y sbt

# Copy in build scripts
COPY $TOPLEVEL/Makefile $DUT/

WORKDIR $DUT
CMD ["run"]
