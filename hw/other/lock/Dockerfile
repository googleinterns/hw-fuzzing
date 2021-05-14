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

# Docker image for fuzzing various lock circuits with AFL
ARG FUZZER=sim
FROM hw-fuzzing/base-${FUZZER}
MAINTAINER trippel@umich.edu

# Install Rust compiler/build system for HDL generator
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="$PATH:/root/.cargo/bin"

# Test that TOPLEVEL argument was passed
ARG TOPLEVEL
RUN test -n "$TOPLEVEL"

# Create DUT directory
ENV DUT=$HW/$TOPLEVEL
RUN mkdir $DUT

# Copy in HDL and testbench
COPY hdl_generator $DUT/hdl_generator
ENV PATH="${PATH}:${DUT}/hdl_generator"
COPY hdl $DUT/hdl
COPY tb $DUT/tb
COPY seeds $DUT/seeds

# Copy in build scripts
COPY Makefile $DUT/

WORKDIR $DUT
CMD ["run"]
