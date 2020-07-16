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
    # Build fuzzing Docker infrastructure
    #docker build --pull -t hw-fuzzing/base-image $@ $HW_FUZZING/infra/base-image
    #docker build -t hw-fuzzing/base-verilator $@ $HW_FUZZING/infra/base-verilator
    #docker build -t hw-fuzzing/base-clang-10.0.0 $@ $HW_FUZZING/infra/base-clang-10.0.0
    #docker build -t hw-fuzzing/base-clang-4.0.0 $@ $HW_FUZZING/infra/base-clang-4.0.0
    #docker build -t hw-fuzzing/base-afl $@ $HW_FUZZING/infra/base-afl
    #docker build -t hw-fuzzing/base-afl-fork $@ $HW_FUZZING/infra/base-afl-fork
    #docker build -t hw-fuzzing/base-aflgo $@ $HW_FUZZING/infra/base-aflgo
    docker build -t hw-fuzzing/base-aflgo-fork $@ $HW_FUZZING/infra/base-aflgo-fork

    # Build circuit build/sim Docker infrastructure
    #docker build --pull -t hw-fuzzing/base-opentitan $@ $HW_FUZZING/infra/base-opentitan
fi
