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

# Docker image for circuit verification

FROM hw-fuzzing/base-verilator
MAINTAINER trippel@umich.edu

# Setup directory structure
ENV HW=$SRC/hw
RUN mkdir $HW

# Copy over hardware fuzzing build scripts and common test bench code
COPY common.mk exe.mk $HW/
COPY tb $HW/tb
COPY scripts/ $SCRIPTS/
COPY python-requirements.txt $SRC/python-requirements.txt

# Install python dependencies
RUN apt-get install -y git xxd
RUN python3 -m pip install -r $SRC/python-requirements.txt
RUN apt-get remove --purge -y git && apt-get autoremove -y
RUN rm $SRC/python-requirements.txt
