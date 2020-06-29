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

trap sigint_handler SIGINT

function sigint_handler() {
    CHECKPOINT=false
    echo "Terminating checkpointing process ..."
}

# wait for AFLGo to startup
sleep 8s

# start checkpoint the queue
i=0
CHECKPOINT=true
while $CHECKPOINT; do
    # sleep
    sleep ${CHECKPOINT_INTERVAL_MINS}m

    echo "Checkpointing ($i) AFLGo outputs ..."

    # create checkpoint directory
    AFLOUT_DIR=$BK_DIR/afl_out.$i
    mkdir $AFLOUT_DIR
    mkdir $AFLOUT_DIR/queue

    # copy fuzz_bitmap
    if [[ -f "afl_out/fuzz_bitmap" ]]; then
        cp afl_out/fuzz_bitmap $AFLOUT_DIR/
    fi

    # copy fuzzer_stats
    if [[ -f "afl_out/fuzzer_stats" ]]; then
        cp afl_out/fuzzer_stats $AFLOUT_DIR/
    fi

    # copy plot_data
    if [[ -f "afl_out/fuzz_bitmap" ]]; then
        cp afl_out/plot_data $AFLOUT_DIR/
    fi

    # copy input queue
    find afl_out/queue -not -type d -exec cp "{}" $AFLOUT_DIR/queue/ ";"

    # update index counter
    i=$((i + 1))
done
