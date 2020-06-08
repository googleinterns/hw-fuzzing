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

# Docker image with AFLGo installed.

FROM hw-fuzzing/base-clang
MAINTAINER ttrippel@google.com

# Putting installation steps in a script reduces the number of intermediate
# layers generated from the Dockerfile.
COPY checkout_build_install_aflgo.sh /root/
RUN /root/checkout_build_install_aflgo.sh
RUN rm /root/checkout_build_install_aflgo.sh

# Setup the environment.
ENV CC "$SRC/aflgo/afl-clang-fast"
ENV CXX "$SRC/aflgo/afl-clang-fast++"
ENV CCC "$SRC/aflgo/afl-clang-fast++"
#ENV CFLAGS "-O1 -fno-omit-frame-pointer -gline-tables-only -DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION"
#ENV CXXFLAGS_EXTRA "-stdlib=libc++"
ENV CFLAGS ""
ENV CXXFLAGS_EXTRA "-std=c++11"
ENV CXXFLAGS "$CFLAGS $CXXFLAGS_EXTRA"

# Set working directory
WORKDIR $SRC
