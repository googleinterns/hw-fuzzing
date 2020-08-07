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

FROM gcr.io/hardware-fuzzing/base-clang-10.0.0
MAINTAINER ttrippel@google.com

# Add Verilator to PATH
ENV PATH="$PATH:$VERILATOR_ROOT/bin"

# Copy over circuit build scripts
ENV CIRCUITS=$SRC/circuits
RUN mkdir $CIRCUITS
COPY common.mk exe.mk $CIRCUITS/
COPY tb $CIRCUITS/tb
COPY save_and_shutdown $SCRIPTS/
