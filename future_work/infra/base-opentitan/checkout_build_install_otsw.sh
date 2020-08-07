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

# OT SW dependencies
OT_PACKAGES="\
    autoconf \
    bison \
    build-essential \
    clang-format \
    curl \
    doxygen \
    flex \
    g++ \
    git \
    libelf1 \
    libelf-dev \
    libftdi1-2 \
    libftdi1-dev \
    libssl-dev \
    libusb-1.0-0 \
    make \
    ninja-build \
    pkgconf \
    srecord \
    tree \
    xsltproc \
    zlib1g-dev"

# Install dependencies
apt-get install -y $OT_PACKAGES

# Install Python 3 (>= 3.6)
python3 \
python3-pip \
python3-setuptools \
python3-wheel \
python3-yaml \

# Clone the OT repo
cd $SRC
git clone https://github.com/lowRISC/opentitan.git
cd opentitan
export OT_ROOT=`pwd`

# Install Python3 dependencies
pip3 install --upgrade pip
which python
python3 --version
#pip3 install --user -r python-requirements.txt
#export PATH="$PATH:~/.local/bin"

# Install RISC-V compiler toolchain to /tools/riscv
#./util/get-toolchain.py

## Build Verilator from source
#cd $SRC && git clone https://git.veripool.org/git/verilator
#cd verilator
#autoconf
#export VERILATOR_ROOT=`pwd`
#./configure
#make

## Remove installation dependencies to shrink image size
#apt-get remove --purge -y $VLT_INSTALL_PACKAGES
#apt-get autoremove -y

