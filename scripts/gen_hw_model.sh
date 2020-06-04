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

# Build AES model
echo "-------------------------------------------------------------------------"
echo "Building SW model of AES core for fuzzing ..."
echo "-------------------------------------------------------------------------"
cd $SRC/hw-fuzzing/circuits/aes_128

# Verilate the HDL to generate C++ model
echo "Verilating the HDL..."
make
echo "Done!"
echo "------------------------------------------------------------------------"

# Generate targtes to fuzz
echo "Generating targets to fuzz..."
python3 $SRC/$PROJECT/scripts/gen_bb_targets.py $TMP_DIR/BBtargets.txt
cp $TMP_DIR/BBtargets.txt $OUT
if [ $(cat $TMP_DIR/BBtargets.txt | wc -l) -eq 0 ]; then
    echo "#########################################################################"
    echo -e "# \e[1;31mAborting ..\e[0m -- No fuzz targets generated for $PROJECT."
    echo "#########################################################################"
    rm -rf $TMP_DIR
    exit 1
fi
cat $TMP_DIR/BBtargets.txt
echo "------------------------------------------------------------------------"

# Compile/Instrument the HW model
#CXXFLAGS="\
    #-fno-omit-frame-pointer \
    #-gline-tables-only \
    #-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION \
    #-fsanitize=address \
    #-fsanitize-address-use-after-scope \
    #-fsanitize-coverage=trace-pc-guard \
    #$ADDITIONAL"
CXXFLAGS="$ADDITIONAL" LDFLAGS="$ADDITIONAL" make exe

echo "-------------------------------------------------------------------------"
echo "Done!"
echo "-------------------------------------------------------------------------"
