# Copyright 2020 Timothy Trippel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Docker image with Clang version 11.0.0 installed.

FROM hw-fuzzing/base-image
MAINTAINER trippel@umich.edu

# Putting installation steps in a script reduces the number of intermediate
# layers generated from the Dockerfile.
COPY checkout_build_install_llvm.sh /root/
RUN /root/checkout_build_install_llvm.sh
RUN rm /root/checkout_build_install_llvm.sh

# Install LLVMgold into bfd-plugins
RUN cp /usr/local/lib/libLTO.so /usr/lib/bfd-plugins
RUN cp /usr/local/lib/LLVMgold.so /usr/lib/bfd-plugins
