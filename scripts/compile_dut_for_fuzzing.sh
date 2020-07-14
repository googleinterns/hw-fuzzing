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

LINE_SEP="-------------------------------------------------------------------"

################################################################################
################################################################################
## Set build flags
################################################################################
################################################################################
echo "Setting compiler/linker flags..."

# Set fuzzer compiler
if [[ $FUZZER == "afl" ]]; then
    export CC="$SRC/AFL/afl-clang-fast"
    export CXX="$SRC/AFL/afl-clang-fast++"
    export CCC="$SRC/AFL/afl-clang-fast++"
elif [[ $FUZZER == "aflgo" ]]; then
    export CC="$SRC/aflgo/afl-clang-fast"
    export CXX="$SRC/aflgo/afl-clang-fast++"
    export CCC="$SRC/aflgo/afl-clang-fast++"
else
    echo -e "\e[1;31mAborting ... unsupported fuzzer: $FUZZER.\e[0m"
    exit 1
fi

# Set Verilator compiler
export VLT_CXX="clang++"

# Disable Verilator VCD tracing during fuzzing
export DISABLE_VCD_TRACING=1

# Build code with source-line table mappings -- same as "-g"
SOURCE_MAPPINGS_FLAGS="-gline-tables-only"

# Set compiler/linker flags
export CFLAGS="$SOURCE_MAPPINGS_FLAGS"
export CXXFLAGS="$SOURCE_MAPPINGS_FLAGS"
export VLT_CXXFLAGS=""
export LDFLAGS="$LDFLAGS"

echo "Done!"

################################################################################
################################################################################
## Switch to experiment directory and create bin/build directories
################################################################################
################################################################################
echo $LINE_SEP
echo "Switching to experiment directory and creating bin directory ..."

# Move to experiment directory
cd $SRC/circuits/$CORE

# Make a build directory to store fuzzer compiler inputs/outputs
BUILD_DIR=$SRC/circuits/$CORE/$EXP_DATA_PATH/build
mkdir -p $BUILD_DIR

# Make a bin directory to store instrumented EXEs
BIN_DIR=$SRC/circuits/$CORE/$EXP_DATA_PATH/bin
mkdir -p $BIN_DIR

echo "Done!"

################################################################################
################################################################################
## Install Verilator test bench dependencies
################################################################################
################################################################################
echo $LINE_SEP
echo "Installing dependencies for $CORE test bench ..."

source tb_deps.sh
if [ -z $TB_DEPS ]; then
    echo "No dependencies to install."
else
    echo "Installing: $TB_DEPS"
    apt-get install -y $TB_DEPS
fi
echo "Done!"

################################################################################
################################################################################
## Build SW model of HDL using Verilator
################################################################################
################################################################################
echo $LINE_SEP
echo "Building SW model of $CORE core for fuzzing ..."

MODEL_DIR=$SRC/circuits/$CORE/$EXP_DATA_PATH/model
MODEL_DIR=$MODEL_DIR make verilate

echo "Done!"

################################################################################
################################################################################
## Do preprocessing (if necessary)
################################################################################
################################################################################
if [ $FUZZER == "aflgo" ]; then
    echo $LINE_SEP
    echo "Doing AFLGo preprocessing ..."

    # Skip preprocessing if distance.cfg.txt exists already
    if [ -f $BIN_DIR/distance.cfg.txt ]; then
        DO_POSTPROCESS=0

        echo "Setting compiler flags..."
        export CFLAGS="$CFLAGS -distance=$BIN_DIR/distance.cfg.txt"
        export CXXFLAGS="$CXXFLAGS -distance=$BIN_DIR/distance.cfg.txt"
        export LDFLAGS="$LDFLAGS -distance=$BIN_DIR/distance.cfg.txt"
    else
        DO_POSTPROCESS=1

        # Make backup copy of base compiler/linker flags
        COPY_CFLAGS=$CFLAGS
        COPY_CXXFLAGS=$CXXFLAGS
        COPY_LDFLAGS=$LDFLAGS

        # Generate targets to fuzz
        echo "Generating targets to fuzz..."
        AFLGO_BB_TARGETS=$BUILD_DIR/BBtargets.txt
        python3 $SRC/circuits/$CORE/aflgo_gen_bb_targets.py $AFLGO_BB_TARGETS

        # Check if at least one fuzz target was generated
        if [ $(cat $AFLGO_BB_TARGETS | wc -l) -eq 0 ]; then
            echo -e "\e[1;31mAborting ... No BB targets to fuzz for $CORE.\e[0m"
            rm -rf $BIN_DIR
            rm -rf $BUILD_DIR
            rm -rf $MODEL_DIR
            exit 1
        fi

        # Print generated fuzz targets
        echo "AFLGo Fuzz Targets:"
        cat $AFLGO_BB_TARGETS

        # Set AFLGo compiler flags
        echo "Setting compiler flags..."
        AFLGO_TARGET_FLAGS="-targets=$AFLGO_BB_TARGETS -outdir=$BUILD_DIR"
        AFLGO_LINKER_FLAGS="-flto -fuse-ld=gold -Wl,-plugin-opt=save-temps"
        AFLGO_FLAGS="$AFLGO_TARGET_FLAGS $AFLGO_LINKER_FLAGS"
        export CFLAGS="$CFLAGS $AFLGO_FLAGS"
        export CXXFLAGS="$CXXFLAGS $AFLGO_FLAGS"
        export LDFLAGS="$LDFLAGS $AFLGO_FLAGS"
        echo "Done!"
    fi
else
    DO_POSTPROCESS=0
fi

# Print Fuzzer/Compiler/Linker Configurations
echo $LINE_SEP
echo "Fuzzer/Compiler Configurations:"
echo "FUZZER=$FUZZER"
echo "CC=$CC"
echo "CXX=$CXX"
echo "CFLAGS=$CFLAGS"
echo "CXXFLAGS=$CXXFLAGS"
echo "LDFLAGS=$LDFLAGS"

################################################################################
################################################################################
## First (and potentially only) Compile Pass
################################################################################
################################################################################
echo $LINE_SEP

if [ $DO_POSTPROCESS -eq 1 ]; then
    echo "Computing CG/CFG of $CORE SW model (for AFLGo) ..."
else
    echo "Compiling/Instrumenting the $CORE SW model ..."
fi

MODEL_DIR=$MODEL_DIR BUILD_DIR=$BUILD_DIR BIN_DIR=$BIN_DIR make exe

echo "Done!"

################################################################################
################################################################################
## Do AFLGo postprocessing
################################################################################
################################################################################
if [ $DO_POSTPROCESS -eq 1 ]; then
    echo $LINE_SEP
    echo "Doing AFLGo postprocessing ..."

    # Check if AFLGo control flow graph extraction was successfull and fuzz
    # targets were found
    if [ $(grep -Ev "^$" $BUILD_DIR/Ftargets.txt | wc -l) -eq 0 ]; then
        echo -e "\e[1;31mAborting ... No function targets found in model.\e[0m"
        if [ -z "${DEBUG-}" ]; then
            rm -rf $BIN_DIR
            rm -rf $BUILD_DIR
            rm -rf $MODEL_DIR
        fi
        exit 1
    fi

    # Filter BBnames and Fnames
    sleep 0.5
    cat $BUILD_DIR/BBnames.txt | rev | cut -d: -f2- | rev | sort | uniq > \
        $BUILD_DIR/BBnames2.txt && \
        mv $BUILD_DIR/BBnames2.txt $BUILD_DIR/BBnames.txt
    cat $BUILD_DIR/BBcalls.txt | sort | uniq > $BUILD_DIR/BBcalls2.txt && \
        mv $BUILD_DIR/BBcalls2.txt $BUILD_DIR/BBcalls.txt

    echo "Computing distances to fuzz targets..."
    $SRC/aflgo/scripts/genDistance.sh $BIN_DIR $BUILD_DIR

    # Clean up
    rm $BIN_DIR/*
    cp $BUILD_DIR/distance.cfg.txt $BIN_DIR
    if [ -n "${DEBUG-}" ]; then
        cp $BUILD_DIR/*.txt $BIN_DIR
    fi
    rm -rf $BUILD_DIR/*

    # Restore compiler/linker flags
    export CFLAGS="$COPY_CFLAGS -distance=$BIN_DIR/distance.cfg.txt"
    export CXXFLAGS="$COPY_CXXFLAGS -distance=$BIN_DIR/distance.cfg.txt"
    export LDFLAGS="$COPY_LDFLAGS -distance=$BIN_DIR/distance.cfg.txt"

    # Second compiler pass (instrumentation happens here)
    echo "Compiling/Instrumenting the $CORE SW model ..."
    MODEL_DIR=$MODEL_DIR BUILD_DIR=$BUILD_DIR BIN_DIR=$BIN_DIR make exe
    echo "Done!"
fi

################################################################################
################################################################################
## Clean up object files and Verilator output
################################################################################
################################################################################
echo $LINE_SEP
echo "Cleaning up ..."

if [ -z "${DEBUG-}" ]; then
    rm -rf $BUILD_DIR
    rm -rf $MODEL_DIR
fi

echo -e "\e[1;32mBUILD & INSTRUMENTATION SUCCESSFUL -- Done!\e[0m"
exit 0
