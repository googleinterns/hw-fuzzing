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
    git \
    subversion \
    python2.7 \
    binutils-gold \
    binutils-dev \
    wget"
apt-get install -y $LLVM_DEP_PACKAGES

# Download LLVM version 4.0 as instructed by AFLGo documentation.
cd $SRC && wget http://releases.llvm.org/4.0.0/llvm-4.0.0.src.tar.xz
tar xf llvm-4.0.0.src.tar.xz
mv llvm-4.0.0.src llvm
cd $SRC/llvm/tools && wget http://releases.llvm.org/4.0.0/cfe-4.0.0.src.tar.xz
tar xf cfe-4.0.0.src.tar.xz
mv cfe-4.0.0.src clang
cd $SRC/llvm/projects && wget http://releases.llvm.org/4.0.0/compiler-rt-4.0.0.src.tar.xz
tar xf compiler-rt-4.0.0.src.tar.xz
mv compiler-rt-4.0.0.src compiler-rt
cd $SRC/llvm/projects && wget http://releases.llvm.org/4.0.0/libcxx-4.0.0.src.tar.xz
tar xf libcxx-4.0.0.src.tar.xz
mv libcxx-4.0.0.src libcxx
cd $SRC/llvm/projects && wget http://releases.llvm.org/4.0.0/libcxxabi-4.0.0.src.tar.xz
tar xf libcxxabi-4.0.0.src.tar.xz
mv libcxxabi-4.0.0.src libcxxabi

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

mkdir -p /tmp/msan
cd /tmp/msan
cmake -G "Ninja" \
      -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
      -DLLVM_USE_SANITIZER=Memory -DCMAKE_INSTALL_PREFIX=/usr/msan/ \
      -DLIBCXX_ENABLE_SHARED=OFF -DLIBCXX_ENABLE_STATIC_ABI_LIBRARY=ON \
      -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="X86" \
      $SRC/llvm
ninja cxx
ninja install-cxx
rm -rf /tmp/msan

# Install LLVMgold into bfd-plugins
mkdir /usr/lib/bfd-plugins
cp /usr/local/lib/libLTO.so /usr/lib/bfd-plugins
cp /usr/local/lib/LLVMgold.so /usr/lib/bfd-plugins

# Cleanup
rm -rf $SRC/llvm-4.0.0.src.tar.xz
rm -rf $SRC/llvm
apt-get remove --purge -y $LLVM_DEP_PACKAGES
apt-get autoremove -y
