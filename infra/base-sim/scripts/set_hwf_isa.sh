#!/bin/bash -eu
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

# Check for HW Fuzzing ISA Identifiers
if [[ ${OPCODE_TYPE-} == "constant" ]]; then
  if [ -z ${TB_CXXFLAGS-} ]; then
    TB_CXXFLAGS="-DOPCODE_TYPE_MAPPED=1"
  else
    TB_CXXFLAGS="$TB_CXXFLAGS -DOPCODE_TYPE_MAPPED=1"
  fi
fi
if [[ ${INSTR_TYPE-} == "fixed" ]]; then
  if [ -z ${TB_CXXFLAGS-} ]; then
    TB_CXXFLAGS="-DINSTR_TYPE_FIXED=1"
  else
    TB_CXXFLAGS="$TB_CXXFLAGS -DINSTR_TYPE_FIXED=1"
  fi
fi
if [[ ${TERMINATE_ON_INVALID_OPCODE-} == "1" ]]; then
  if [ -z ${TB_CXXFLAGS-} ]; then
    TB_CXXFLAGS="-DTERMINATE_ON_INVALID_OPCODE=1"
  else
    TB_CXXFLAGS="$TB_CXXFLAGS -DTERMINATE_ON_INVALID_OPCODE=1"
  fi
fi
echo "TB_CXXFLAGS: $TB_CXXFLAGS"
export TB_CXXFLAGS
