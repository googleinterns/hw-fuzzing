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

# Switch to CORE directory
cd $SRC/circuits/$CORE
make clean

# Build SW model of HDL using Verilator
echo "========================================================================="
echo "Installing dependencies for $CORE test bench ..."
echo "-------------------------------------------------------------------------"
source tb_deps.sh
echo "Test Bench Dependencies: $TB_DEPS"
apt-get install -y $TB_DEPS
echo "------------------------------------------------------------------------"
echo "Done!"

# Build SW model of HDL using Verilator
echo "========================================================================="
echo "Building SW model of $CORE core for fuzzing ..."
echo "-------------------------------------------------------------------------"
make
echo "------------------------------------------------------------------------"
echo "Done!"

# Do AFLGo preprocessing
echo "========================================================================="
echo "Doing AFLGo preprocessing ..."
echo "-------------------------------------------------------------------------"

# Skip preprocessing if distance.cfg.txt exists already
if [ -f $OUT/distance.cfg.txt ]; then
    DO_POSTPROCESS=0

    export CFLAGS="$CFLAGS -distance=$OUT/distance.cfg.txt"
    export CXXFLAGS="$CXXFLAGS -distance=$OUT/distance.cfg.txt"
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

    # Generate targets to fuzz
echo "-------------------------------------------------------------------------"
echo "Generating targets to fuzz..."
    python3 $SCRIPTS/gen_bb_targets.py $TMP_DIR/BBtargets.txt
    cp $TMP_DIR/BBtargets.txt $OUT
    AFLGO_FUZZ_TARGETS=$TMP_DIR/BBtargets.txt

    # Check if at least one fuzz target was generated
    if [ $(cat $TMP_DIR/BBtargets.txt | wc -l) -eq 0 ]; then
echo -e "# \e[1;31mAborting ..\e[0m -- No targets to fuzz for $CORE."
        rm -rf $TMP_DIR
        exit 1
    fi

    # Print generated fuzz targets
echo "-------------------------------------------------------------------------"
echo "AFLGo Fuzz Targets:"
    cat $TMP_DIR/BBtargets.txt

    # Set AFLGo compiler flags
    AFLGO_TARGET_FLAGS="-targets=$AFLGO_FUZZ_TARGETS -outdir=$TMP_DIR"
    AFLGO_LINKER_FLAGS="-flto -fuse-ld=gold -Wl,-plugin-opt=save-temps"
    AFLGO_FLAGS="$AFLGO_TARGET_FLAGS $AFLGO_LINKER_FLAGS"
    export CFLAGS="$CFLAGS $AFLGO_FLAGS"
    export CXXFLAGS="$CXXFLAGS $AFLGO_FLAGS"
    export LDFLAGS="$CXXFLAGS $AFLGO_FLAGS"
fi

echo "-------------------------------------------------------------------------"
echo "CC=$CC"
echo "CXX=$CXX"
echo "CFLAGS=$CFLAGS"
echo "CXXFLAGS=$CXXFLAGS"
echo "-------------------------------------------------------------------------"
echo "Done!"

# Compile/Instrument the SW model of the CORE
echo "========================================================================="
echo "Compiling/Instrumenting the SW model of $CORE ..."
echo "-------------------------------------------------------------------------"
make exe
#CXXFLAGS="\
    #-fno-omit-frame-pointer \
    #-gline-tables-only \
    #-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION \
    #-fsanitize=address \
    #-fsanitize-address-use-after-scope \
    #-fsanitize-coverage=trace-pc-guard \
    #$ADDITIONAL"
echo "-------------------------------------------------------------------------"
echo "Done!"
echo "========================================================================="
