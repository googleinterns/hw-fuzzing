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
## Set build flags
################################################################################
################################################################################
echo "========================================================================="
echo "Setting compiler/linker flags..."
echo "-------------------------------------------------------------------------"

# Default build flags for various sanitizers
SANITIZER_FLAGS_address="-fsanitize=address "\
"-fsanitize-address-use-after-scope"
SANITIZER_FLAGS_undefined="-fsanitize=bool,"\
"array-bounds,"\
"float-divide-by-zero,"\
"function,"\
"integer-divide-by-zero,"\
"return,"\
"shift,"\
"signed-integer-overflow,"\
"vla-bound,"\
"vptr "\
"-fno-sanitize-recover=undefined"
SANITIZER_FLAGS_memory="-fsanitize=memory "\
"-fsanitize-memory-track-origins"

# Default build flags for coverage
#COVERAGE_FLAGS="-fsanitize-coverage=trace-pc-guard,trace-cmp"
COVERAGE_FLAGS="-fsanitize-coverage=trace-pc-guard"

# Workaround ASAN false positive: https://github.com/google/sanitizers/issues/647
ASAN_OPTIONS="detect_odr_violation=0"

# Set sanitizer flags
if [ -z "${SANITIZER_FLAGS-}" ]; then
  FLAGS_VAR="SANITIZER_FLAGS_${SANITIZER}"
  export SANITIZER_FLAGS=${!FLAGS_VAR-}
fi

# If using memory sanitizer, use the one installed with Clang 4.0.0
if [[ $SANITIZER_FLAGS = *sanitize=memory* ]]; then
    # Take all libraries from lib/msan
    cp -R /usr/msan/lib/* /usr/lib/
fi

# Set coverage tracing flag overrides
COVERAGE_FLAGS_VAR="COVERAGE_FLAGS_$SANITIZER"
if [[ -n ${!COVERAGE_FLAGS_VAR-} ]]; then
  export COVERAGE_FLAGS="${!COVERAGE_FLAGS_VAR}"
fi

# Set compiler/linker flags
export CFLAGS="$CFLAGS $SANITIZER_FLAGS $COVERAGE_FLAGS"
export CXXFLAGS="$CXXFLAGS $SANITIZER_FLAGS $COVERAGE_FLAGS"
export LDFLAGS="$LDFLAGS $SANITIZER_FLAGS $COVERAGE_FLAGS"

# Print Compiler/Linker Flags
echo "Compiler/Linker Flags:"
echo "CC=$CC"
echo "CXX=$CXX"
echo "CFLAGS=$CFLAGS"
echo "CXXFLAGS=$CXXFLAGS"
echo "LDFLAGS=$LDFLAGS"
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## Switch to CORE directory and cleanup old build
################################################################################
################################################################################
echo "========================================================================="
echo "Cleaning up old $CORE build ..."
echo "-------------------------------------------------------------------------"
cd $SRC/circuits/$CORE
make clean
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## Install Verilator test bench dependencies
################################################################################
################################################################################
echo "========================================================================="
echo "Installing dependencies for $CORE test bench ..."
echo "-------------------------------------------------------------------------"
source tb_deps.sh
if [ -z $TB_DEPS ]; then
    echo "No dependencies to install."
else
    echo "Installing: $TB_DEPS"
    apt-get install -y $TB_DEPS
fi
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## Build SW model of HDL using Verilator
################################################################################
################################################################################
echo "========================================================================="
echo "Building SW model of $CORE core for fuzzing ..."
echo "-------------------------------------------------------------------------"
make verilate
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## Do AFLGo preprocessing
################################################################################
################################################################################
echo "========================================================================="
echo "Doing AFLGo preprocessing ..."
echo "-------------------------------------------------------------------------"

# Skip preprocessing if distance.cfg.txt exists already
if [ -f $OUT/distance.cfg.txt ]; then
    DO_POSTPROCESS=0

    echo "Setting compiler flags..."
    export CFLAGS="$CFLAGS -distance=$OUT/distance.cfg.txt"
    export CXXFLAGS="$CXXFLAGS -distance=$OUT/distance.cfg.txt"
    export LDFLAGS="$LDFLAGS -distance=$OUT/distance.cfg.txt"
else
    DO_POSTPROCESS=1

    # Make a temporary directory to store AFLGo compiler inputs/outputs
    TMP_DIR=$WORK/tmp
    i=0
    while [ -d $TMP_DIR ]; do
      TMP_DIR=$WORK/tmp.$i
      i=$((i + 1))
    done
    mkdir $TMP_DIR

    # Make backup copy of base compiler/linker flags
    COPY_CFLAGS=$CFLAGS
    COPY_CXXFLAGS=$CXXFLAGS
    COPY_LDFLAGS=$LDFLAGS

    # Generate targets to fuzz
    echo "Generating targets to fuzz..."
    python3 $SCRIPTS/gen_bb_targets.py $TMP_DIR/BBtargets.txt
    AFLGO_BB_TARGETS=$TMP_DIR/BBtargets.txt

    # Check if at least one fuzz target was generated
    if [ $(cat $TMP_DIR/BBtargets.txt | wc -l) -eq 0 ]; then
        echo -e "\e[1;31mAborting ... No BB targets to fuzz for $CORE.\e[0m"
        rm -rf $TMP_DIR
        exit 1
    fi

    # Print generated fuzz targets
    echo "AFLGo Fuzz Targets:"
    cat $TMP_DIR/BBtargets.txt

    # Set AFLGo compiler flags
    echo "Setting compiler flags..."
    AFLGO_TARGET_FLAGS="-targets=$AFLGO_BB_TARGETS -outdir=$TMP_DIR"
    AFLGO_LINKER_FLAGS="-flto -fuse-ld=gold -Wl,-plugin-opt=save-temps"
    AFLGO_FLAGS="$AFLGO_TARGET_FLAGS $AFLGO_LINKER_FLAGS"
    export CFLAGS="$CFLAGS $AFLGO_FLAGS"
    export CXXFLAGS="$CXXFLAGS $AFLGO_FLAGS"
    export LDFLAGS="$LDFLAGS $AFLGO_FLAGS"
fi

# Print Compiler/Linker Flags
echo "Compiler/Linker Flags:"
echo "CC=$CC"
echo "CXX=$CXX"
echo "CFLAGS=$CFLAGS"
echo "CXXFLAGS=$CXXFLAGS"
echo "LDFLAGS=$LDFLAGS"
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## First Compile Pass
################################################################################
################################################################################
echo "========================================================================="
if [ $DO_POSTPROCESS -eq 1 ]; then
    echo "Computing CG/CFG of $CORE SW model ..."
else
    echo "Compiling/Instrumenting the $CORE SW model ..."
fi
echo "-------------------------------------------------------------------------"
BUILD_DIR=$TMP_DIR BIN_DIR=$OUT make exe
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## Do AFLGo postprocessing
################################################################################
################################################################################
if [ $DO_POSTPROCESS -eq 1 ]; then
echo "========================================================================="
echo "Doing AFLGo postprocessing ..."
echo "-------------------------------------------------------------------------"
    # Check if AFLGo control flow graph extraction was successfull and fuzz
    # targets were found
    if [ $(grep -Ev "^$" $TMP_DIR/Ftargets.txt | wc -l) -eq 0 ]; then
        echo -e "\e[1;31mAborting ... No function targets found in model.\e[0m"
        if [ -z "${DEBUG-}" ]; then
            rm $OUT/*
            rm -rf $TMP_DIR
        fi
        exit 1
    fi

    # Filter BBnames and Fnames
    sleep 0.5
    cat $TMP_DIR/BBnames.txt | rev | cut -d: -f2- | rev | sort | uniq > \
        $TMP_DIR/BBnames2.txt && mv $TMP_DIR/BBnames2.txt $TMP_DIR/BBnames.txt
    cat $TMP_DIR/BBcalls.txt | sort | uniq > $TMP_DIR/BBcalls2.txt && \
        mv $TMP_DIR/BBcalls2.txt $TMP_DIR/BBcalls.txt

    echo "Computing distances to fuzz targets..."
    $SRC/aflgo/scripts/genDistance.sh $OUT $TMP_DIR

    # Clean up
    rm $OUT/*
    cp $TMP_DIR/distance.cfg.txt $OUT
    if [ -n "${DEBUG-}" ]; then
        cp $TMP_DIR/*.txt $OUT
    fi
    rm -rf $TMP_DIR/*

    # Restore compiler/linker flags
    export CFLAGS="$COPY_CFLAGS -distance=$OUT/distance.cfg.txt"
    export CXXFLAGS="$COPY_CXXFLAGS -distance=$OUT/distance.cfg.txt"
    export LDFLAGS="$COPY_LDFLAGS -distance=$OUT/distance.cfg.txt"

    # Second compiler pass (instrumentation happens here)
    echo "Compiling/Instrumenting the $CORE SW model ..."
    BUILD_DIR=$TMP_DIR BIN_DIR=$OUT make exe
fi
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## Clean up object files and Verilator output
################################################################################
################################################################################
echo "========================================================================="
echo "Cleaning up ..."
if [ -z "${DEBUG-}" ]; then
    rm -rf $WORK/
    make clean-vlt
fi
echo "-------------------------------------------------------------------------"
echo -e "\e[1;32mBUILD & INSTRUMENTATION SUCCESSFUL -- Done!\e[0m"
echo "========================================================================="
