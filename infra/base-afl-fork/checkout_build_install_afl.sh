#!/bin/bash -eu
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
AFL_DEP_PACKAGES="\
    git \
    python3-dev \
    python3-pip"
apt-get update
apt-get install -y $AFL_DEP_PACKAGES
pip3 install --upgrade pip

# Set Python3 as default
ln -s $(which python3) /usr/bin/python

# Clone AFL
echo "Checking out AFL ..."
cd $SRC && git clone --depth 1 https://github.com/timtrippel/AFL.git

# Build AFL from source
echo "Compiling AFL ..."
export CC=clang
export CXX=clang++
export CCC=clang++
cd AFL && make clean all
cd llvm_mode && make clean all
echo " done."
