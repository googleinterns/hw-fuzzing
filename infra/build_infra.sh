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
    # Build Docker infrastructure
    docker build --pull -t hw-fuzzing/base-image $@ infra/base-image
    docker build -t hw-fuzzing/base-verilator $@ infra/base-verilator
    docker build -t hw-fuzzing/base-clang $@ infra/base-clang
    docker build -t hw-fuzzing/base-aflgo $@ infra/base-aflgo

    # Create directories for compiling/fuzzing outputs/work
    mkdir -p $HW_FUZZING/out
    mkdir -p $HW_FUZZING/work
fi
