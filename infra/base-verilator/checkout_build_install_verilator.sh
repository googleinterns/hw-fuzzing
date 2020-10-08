#!/bin/bash -eux
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

# Install dependencies
VLT_INSTALL_PACKAGES="\
    git \
    autoconf \
    flex \
    bison"
apt-get install -y $VLT_INSTALL_PACKAGES

# Build latest version of Verilator from source
VLT_GITHUB_URL=https://github.com/verilator/verilator.git
cd $SRC && git clone $VLT_GITHUB_URL
cd verilator
# Use last verified commit on Oct. 8, 2020
git checkout 7be343fd7c885359ac29e50e9732509caf64637d
autoconf
export VERILATOR_ROOT=$(pwd)
./configure
make -j 4

# Remove installation dependencies to shrink image size
apt-get remove --purge -y $VLT_INSTALL_PACKAGES
apt-get autoremove -y
