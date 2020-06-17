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
## Generate AFLGO seeds
################################################################################
################################################################################
echo "========================================================================="
echo "Generating seed test files ..."
echo "-------------------------------------------------------------------------"
cd $SRC/circuits/$CORE
make seed
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## Fuzz the CORE
################################################################################
################################################################################
echo "========================================================================="
echo "Launching fuzzer ..."
echo "-------------------------------------------------------------------------"
$SRC/aflgo/afl-fuzz \
    -d \
    -z exp \
    -c 45m \
    -i afl_in \
    -o afl_out \
    bin/V$CORE @@
echo "-------------------------------------------------------------------------"
echo "Done!"

################################################################################
################################################################################
## Backup fuzzing results
################################################################################
################################################################################
echo "========================================================================="
echo "Backing up fuzzing results ..."
echo "-------------------------------------------------------------------------"
i=0
BK_DIR="fuzz_exp"
while [ -d $BK_DIR ]; do
  BK_DIR=$BK_DIR.$i
  i=$((i + 1))
done
mkdir $BK_DIR
mv afl_in $BK_DIR/
mv afl_out $BK_DIR/
mv build $BK_DIR/
mv bin $BK_DIR/
mv model $BK_DIR/
echo "Done!"
echo "========================================================================="
exit 0
