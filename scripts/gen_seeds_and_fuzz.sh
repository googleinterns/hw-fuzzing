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

################################################################################
################################################################################
## Fuzz the CORE
################################################################################
################################################################################
echo "========================================================================="
echo "Launching fuzzer ..."
echo "-------------------------------------------------------------------------"
cd $SRC/circuits/$CORE/$EXP_DATA_PATH
mkdir logs
#if [[ ! -z ${CHECKPOINT_INTERVAL_MINS-} ]]; then
    #BK_DIR=$BK_DIR CHECKPOINT_INTERVAL_MINS="$CHECKPOINT_INTERVAL_MINS" \
        #source $SCRIPTS/checkpoint_aflgo_output.sh &
    #CHECKPOINTING_PID=$!
#fi

for (( num=1; num <= $NUM_INSTANCES; num++ )); do
    echo "Launching fuzzer instance $num ..."

    # Set parallel option
    if [[ $num -eq 1 ]]; then
        PARALLEL_OPT="-M ${FUZZER_INSTANCE_BASENAME}_${num}"
    else
        PARALLEL_OPT="-S ${FUZZER_INSTANCE_BASENAME}_${num}"
    fi

    # Create logs dir and set logging file names
    STDERR_LOG="logs/${FUZZER_INSTANCE_BASENAME}_${num}.err.log"
    STDOUT_LOG="logs/${FUZZER_INSTANCE_BASENAME}_${num}.out.log"

    # Launch fuzzer
    if [[ -z ${FUZZING_DURATION_MINS-} ]]; then
        $SRC/aflgo/afl-fuzz \
            -z exp \
            -c ${TIME_TO_EXPLOITATION_MINS}m \
            -i $FUZZER_INPUT_DIR \
            -o $FUZZER_OUTPUT_DIR \
            $PARALLEL_OPT \
            bin/V$CORE @@ \
            2> $STDERR_LOG \
            1> $STDOUT_LOG;
    else
        timeout --foreground ${FUZZING_DURATION_MINS}m\
            $SRC/aflgo/afl-fuzz \
            -z exp \
            -c ${TIME_TO_EXPLOITATION_MINS}m \
            -i $FUZZER_INPUT_DIR \
            -o $FUZZER_OUTPUT_DIR \
            $PARALLEL_OPT \
            bin/V$CORE @@ \
            2> $STDERR_LOG \
            1> $STDOUT_LOG;
    fi
done

#if [[ ! -z ${CHECKPOINTING_PID-} ]]; then
    #kill -2 $CHECKPOINTING_PID
    #sleep 0.5s
#fi
echo "-------------------------------------------------------------------------"
echo "Done!"
echo "========================================================================="
exit 0
