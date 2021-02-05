#!/bin/bash -eu
# Copyright 2020 Timothy Trippel
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

ROOT=/home/ttrippel/repos
export DUT_HDL_DIR=$ROOT/opentitan
EXP_BASE_NAME="exp012-cpp-afl"
TOPLEVEL="$1"
EXP_TOPLEVEL="$1"
OPCODES="mapped"
#OPCODES="constant mapped"
FRAMES="variable"
#FRAMES="fixed variable"
# TODO: add early terminate option, if more experiments run on this
#TERMINATE_TYPES="0 1"
TERMINATE_TYPES="0"
TRIALS="9"
#TRIALS="0 1 2 3 4"
KCOV_PATH=$ROOT/kcov/build/src
SCRIPTS=../../infra/base-sim/scripts
HWFUTILS=../../infra/base-sim/hwfutils/hwfutils

# TODO: check if dir exists
mkdir -p $EXP_BASE_NAME-cov-data

if [[ $TOPLEVEL == "rv-timer" ]]; then
  TOPLEVEL="rv_timer"
fi
pushd hw/$TOPLEVEL >/dev/null
for TERMINATE in $TERMINATE_TYPES; do
  for OPCODE in $OPCODES; do
    for FRAME in $FRAMES; do
      for TRIAL in $TRIALS; do
        # Set paths
        if [[ $TERMINATE == "0" ]]; then
          EXP_NAME=${EXP_BASE_NAME}-${EXP_TOPLEVEL}-${OPCODE}-${FRAME}-never-${TRIAL}
        else
          EXP_NAME=${EXP_BASE_NAME}-${EXP_TOPLEVEL}-${OPCODE}-${FRAME}-invalidop-${TRIAL}
        fi
        EXP_PATH=$ROOT/hw-fuzzing/data/${EXP_NAME}
        LOGS_PATH=$EXP_PATH/logs
        OUT_PATH=$EXP_PATH/out

        # Make dir for aggregated data
        AGG_OUT_PATH=$ROOT/hw-fuzzing/$EXP_BASE_NAME-cov-data/$EXP_NAME/logs
        if [ -d $AGG_OUT_PATH ]; then
          echo -n  "ERROR: data already exists for $(basename "$AGG_OUT_PATH")."
          echo " Aborting!"
          exit 0;          
        fi
        rm -rf $AGG_OUT_PATH
        mkdir -p $AGG_OUT_PATH

        # Set HWF ISA
        export OPCODE_TYPE=$OPCODE
        export INSTR_TYPE=$FRAME
        export TERMINATE_ON_INVALID_OPCODE=$TERMINATE

        ## KCOV
        ## Trace coverage of fuzzer-generated inputs with kcov
        #DUT_HDL_DIR=$DUT_HDL_DIR TOPLEVEL=$TOPLEVEL KCOV_PATH=$KCOV_PATH \
          #LOGS_PATH=$LOGS_PATH OUT_PATH=$OUT_PATH SCRIPTS=$SCRIPTS \
          #$SCRIPTS/run-kcov
        ## Aggregate coverage data
        #python3 $HWFUTILS/extract_kcov.py \
          #--output-dir $AGG_OUT_PATH $TOPLEVEL $LOGS_PATH/kcov

        # LLVM-COV
        # Trace coverage of fuzzer-generated inputs with llvm-cov
        DUT_HDL_DIR=$DUT_HDL_DIR TOPLEVEL=$TOPLEVEL LOGS_PATH=$LOGS_PATH \
          OUT_PATH=$OUT_PATH SCRIPTS=$SCRIPTS $SCRIPTS/run-llvm-cov
        # Aggregate coverage data
        python3 $HWFUTILS/extract_llvm_cov.py --output-dir $AGG_OUT_PATH \
          $TOPLEVEL $LOGS_PATH/llvm-cov

        ## VLT-COV
        ## Trace/Aggregate coverage of fuzzer-generated inputs with Verilator
        #DUT_HDL_DIR=$DUT_HDL_DIR TOPLEVEL=$TOPLEVEL LOGS_PATH=$LOGS_PATH \
          #OUT_PATH=$OUT_PATH AGG_OUT_PATH=$AGG_OUT_PATH SCRIPTS=$SCRIPTS \
          #$SCRIPTS/run-vlt-cov
      done
    done
  done
done
popd >/dev/null
