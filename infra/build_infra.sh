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

DOCKER_IMAGE_BASENAME="hw-fuzzing"

if [ -z ${HW_FUZZING+x} ]; then
  echo "ERROR: Set HW_FUZZING path and try again."
else
  # Build local fuzzing Docker infrastructure
  docker build --pull -t $DOCKER_IMAGE_BASENAME/base-image $@ $HW_FUZZING/infra/base-image
  docker build -t $DOCKER_IMAGE_BASENAME/base-clang-10.0.0 $@ $HW_FUZZING/infra/base-clang-10.0.0
  docker build -t $DOCKER_IMAGE_BASENAME/base-verilator $@ $HW_FUZZING/infra/base-verilator
  cp $HW_FUZZING/python-requirements.txt $HW_FUZZING/hw/
  docker build -t $DOCKER_IMAGE_BASENAME/base-sim $@ $HW_FUZZING/hw
  rm $HW_FUZZING/hw/python-requirements.txt
  docker build -t $DOCKER_IMAGE_BASENAME/base-afl $@ $HW_FUZZING/infra/base-afl
  cp $HW_FUZZING/infra/base-afl/checkout_build_install_afl.sh $HW_FUZZING/infra/base-afl-term-on-crash/
  cp $HW_FUZZING/infra/base-afl/compile-cpp $HW_FUZZING/infra/base-afl-term-on-crash/
  cp $HW_FUZZING/infra/base-afl/compile-cocotb $HW_FUZZING/infra/base-afl-term-on-crash/
  cp $HW_FUZZING/infra/base-afl/fuzz $HW_FUZZING/infra/base-afl-term-on-crash/
  docker build -t $DOCKER_IMAGE_BASENAME/base-afl-term-on-crash $@ $HW_FUZZING/infra/base-afl-term-on-crash
  rm $HW_FUZZING/infra/base-afl-term-on-crash/checkout_build_install_afl.sh
  rm $HW_FUZZING/infra/base-afl-term-on-crash/compile-cpp
  rm $HW_FUZZING/infra/base-afl-term-on-crash/compile-cocotb
  rm $HW_FUZZING/infra/base-afl-term-on-crash/fuzz
fi
