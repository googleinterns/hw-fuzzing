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
LLVM_DEP_PACKAGES="\
    build-essential \
    cmake \
    ninja-build \
    python2.7 \
    binutils-gold \
    binutils-dev \
    wget"
apt-get install -y $LLVM_DEP_PACKAGES

# Download LLVM version 10.0.0

# Download and unpack LLVM
cd $SRC
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/llvm-10.0.0.src.tar.xz
tar xf llvm-10.0.0.src.tar.xz
mv llvm-10.0.0.src llvm

# Download and unpack Clang
cd $SRC/llvm/tools
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/clang-10.0.0.src.tar.xz
tar xf clang-10.0.0.src.tar.xz
mv clang-10.0.0.src clang

# Download and unpack Clang runtime library
cd $SRC/llvm/projects
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/compiler-rt-10.0.0.src.tar.xz
tar xf compiler-rt-10.0.0.src.tar.xz
mv compiler-rt-10.0.0.src compiler-rt

# Download and unpack libc
cd $SRC/llvm/projects
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/libcxx-10.0.0.src.tar.xz
tar xf libcxx-10.0.0.src.tar.xz
mv libcxx-10.0.0.src libcxx

# Download and unpack libc ABI
cd $SRC/llvm/projects
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/libcxxabi-10.0.0.src.tar.xz
tar xf libcxxabi-10.0.0.src.tar.xz
mv libcxxabi-10.0.0.src libcxxabi

# Build & install
mkdir -p /tmp/llvm
cd /tmp/llvm
cmake -G "Ninja" \
      -DLIBCXX_ENABLE_SHARED=OFF -DLIBCXX_ENABLE_STATIC_ABI_LIBRARY=ON \
      -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="X86" \
      -DLLVM_BINUTILS_INCDIR=/usr/include $SRC/llvm
ninja
ninja install
rm -rf /tmp/llvm

# Install LLVMgold into bfd-plugins
mkdir /usr/lib/bfd-plugins
cp /usr/local/lib/libLTO.so /usr/lib/bfd-plugins
cp /usr/local/lib/LLVMgold.so /usr/lib/bfd-plugins

# Cleanup
cd /
rm -rf $SRC/llvm-10.0.0.src.tar.xz
rm -rf $SRC/llvm
apt-get remove --purge -y $LLVM_DEP_PACKAGES
apt-get autoremove -y
