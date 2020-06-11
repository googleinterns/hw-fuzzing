#!/bin/bash
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

if [ -z "$CORE" ]
then
    echo "ERROR: Set CORE to target before proceeding."
else
    echo "Launching container to compile $CORE for fuzzing ..."
    docker run \
        -it \
        --rm \
        --cap-add SYS_PTRACE \
        --name $CORE-compile \
        -e "CORE=$CORE" \
        -e "SANITIZER=address" \
        -v $HW_FUZZING/out/$CORE/:/out \
        -v $HW_FUZZING/work/$CORE/:/work \
        -v $HW_FUZZING/scripts/:/scripts \
        -v $HW_FUZZING/circuits/:/src/circuits \
        -v $HW_FUZZING/third_party:/src/third_party \
        -t hw-fuzzing/base-aflgo \
        bash /scripts/gen_hw_model.sh
fi
