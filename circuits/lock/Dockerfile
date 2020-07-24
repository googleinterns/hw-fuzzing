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

FROM hw-fuzzing/base-circuit
MAINTAINER ttrippel@google.com

# Install Rust compiler/build system for HDL generator
RUN apt-get install -y curl
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
RUN apt-get remove --purge -y curl
RUN apt-get autoremove -y
ENV PATH="$PATH:/root/.cargo/bin"

# Copy in lock HDL or HDL generator, testbench, seeds, build scripts
ENV DUT=$CIRCUITS/lock
RUN mkdir -p $DUT
COPY hdl_generator $DUT/hdl_generator
COPY src $DUT/src
COPY include $DUT/include
COPY seeds $DUT/seeds
COPY Makefile $DUT/
#COPY tb_deps.sh $DUT/
COPY generate_hdl run $SCRIPTS/

# Set working directory
WORKDIR $DUT

# Set entrypoint
CMD ["run"]
