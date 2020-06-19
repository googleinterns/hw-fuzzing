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

# Set compilers
export CC="$SRC/aflgo/afl-clang-fast"
export CXX="$SRC/aflgo/afl-clang-fast++"
export CCC="$SRC/aflgo/afl-clang-fast++"
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

# Print compiler/linker flags
echo "Compiler/Linker Flags:"
echo "CC=$CC"
echo "CXX=$CXX"
echo "CFLAGS=$CFLAGS"
echo "CXXFLAGS=$CXXFLAGS"
echo "VLT_CXXFLAGS=$VLT_CXXFLAGS"
echo "LDFLAGS=$LDFLAGS"
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## Switch to CORE directory and create build directory
################################################################################
################################################################################
echo "========================================================================="
echo "Creating $CORE build directory ..."
echo "-------------------------------------------------------------------------"
# Move to target CORE dir
cd $SRC/circuits/$CORE

# Make a bin directory to store EXEs and AFLGo outputs
i=0
BIN_DIR=$SRC/circuits/$CORE/bin
while [ -d $BIN_DIR ]; do
  BIN_DIR=$SRC/circuits/$CORE/bin.$i
  i=$((i + 1))
done
mkdir $BIN_DIR
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
if [ -f $BIN_DIR/distance.cfg.txt ]; then
    DO_POSTPROCESS=0

    echo "Setting compiler flags..."
    export CFLAGS="$CFLAGS -distance=$BIN_DIR/distance.cfg.txt"
    export CXXFLAGS="$CXXFLAGS -distance=$BIN_DIR/distance.cfg.txt"
    export LDFLAGS="$LDFLAGS -distance=$BIN_DIR/distance.cfg.txt"
else
    DO_POSTPROCESS=1

    # Make a build directory to store AFLGo compiler inputs/outputs
    BUILD_DIR=$SRC/circuits/$CORE/build
    i=0
    while [ -d $BUILD_DIR ]; do
      BUILD_DIR=$SRC/circuits/$CORE/build.$i
      i=$((i + 1))
    done
    mkdir $BUILD_DIR

    # Make backup copy of base compiler/linker flags
    COPY_CFLAGS=$CFLAGS
    COPY_CXXFLAGS=$CXXFLAGS
    COPY_LDFLAGS=$LDFLAGS

    # Generate targets to fuzz
    echo "Generating targets to fuzz..."
    python3 gen_bb_targets.py $BUILD_DIR/BBtargets.txt
    AFLGO_BB_TARGETS=$BUILD_DIR/BBtargets.txt

    # Check if at least one fuzz target was generated
    if [ $(cat $BUILD_DIR/BBtargets.txt | wc -l) -eq 0 ]; then
        echo -e "\e[1;31mAborting ... No BB targets to fuzz for $CORE.\e[0m"
        rm -rf $BUILD_DIR
        exit 1
    fi

    # Print generated fuzz targets
    echo "AFLGo Fuzz Targets:"
    cat $BUILD_DIR/BBtargets.txt

    # Set AFLGo compiler flags
    echo "Setting compiler flags..."
    AFLGO_TARGET_FLAGS="-targets=$AFLGO_BB_TARGETS -outdir=$BUILD_DIR"
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
BUILD_DIR=$BUILD_DIR BIN_DIR=$BIN_DIR make exe
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
    if [ $(grep -Ev "^$" $BUILD_DIR/Ftargets.txt | wc -l) -eq 0 ]; then
        echo -e "\e[1;31mAborting ... No function targets found in model.\e[0m"
        if [ -z "${DEBUG-}" ]; then
            rm -rf $BIN_DIR
            rm -rf $BUILD_DIR
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
    BUILD_DIR=$BUILD_DIR BIN_DIR=$BIN_DIR make exe
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
    rm -rf $BUILD_DIR
    make clean-vlt
fi
echo "-------------------------------------------------------------------------"
echo -e "\e[1;32mBUILD & INSTRUMENTATION SUCCESSFUL -- Done!\e[0m"
echo "========================================================================="
exit 0
