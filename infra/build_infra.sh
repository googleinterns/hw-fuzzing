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

# TODO: Set path to hw-fuzzing in .bashrc
#export HW_FUZZING=/path/to/hw-fuzzing

if [ -z "$HW_FUZZING" ]
then
    echo "ERROR: Set HW_FUZZING path and try again."
else
    # Build local fuzzing Docker infrastructure
    #docker build --pull -t gcr.io/hardware-fuzzing/base-image $@ $HW_FUZZING/infra/base-image
    #docker build -t gcr.io/hardware-fuzzing/base-clang-10.0.0 $@ $HW_FUZZING/infra/base-clang-10.0.0
    docker build -t gcr.io/hardware-fuzzing/base-verilator $@ $HW_FUZZING/infra/base-verilator
    docker build -t gcr.io/hardware-fuzzing/base-sim $@ $HW_FUZZING/circuits
    docker build -t gcr.io/hardware-fuzzing/base-afl $@ $HW_FUZZING/infra/base-afl
    cp $HW_FUZZING/infra/base-afl/compile-cpp $HW_FUZZING/infra/base-afl-term-on-crash/
    cp $HW_FUZZING/infra/base-afl/compile-cocotb $HW_FUZZING/infra/base-afl-term-on-crash/
    cp $HW_FUZZING/infra/base-afl/fuzz $HW_FUZZING/infra/base-afl-term-on-crash/
    docker build -t gcr.io/hardware-fuzzing/base-afl-term-on-crash $@ $HW_FUZZING/infra/base-afl-term-on-crash
fi
