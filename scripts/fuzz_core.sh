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

if [ -z "$CORE" ]; then
    echo "ERROR: Set CORE to target before proceeding."
else
    if [ -z "$BIN_DIR" ]; then
        echo "ERROR: Set BIN_DIR before proceeding."
    else
        echo "Launching container to FUZZ $CORE ..."
        docker run \
            -it \
            --rm \
            --cap-add SYS_PTRACE \
            --name $CORE-fuzz \
            -e BIN_DIR=$BIN_DIR \
            -e CORE=$CORE \
            -e NUM_SEEDS=$NUM_SEEDS \
            -e NUM_TESTS_IN_SEED=$NUM_TESTS_IN_SEED \
            -v $HW_FUZZING/scripts/:/scripts \
            -v $HW_FUZZING/circuits/:/src/circuits \
            -u $(id -u ${USER}):$(id -g ${USER}) \
            -t hw-fuzzing/base-aflgo \
            bash /scripts/gen_seed_and_run_aflgo.sh
    fi
fi
