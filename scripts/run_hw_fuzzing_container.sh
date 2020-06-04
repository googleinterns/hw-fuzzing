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

# TODO: Set path to oss-fuzz and hw-fuzzing in .bashrc
#export OSS=/path/to/oss-fuzz
#export HW_FUZZING=/path/to/hw-fuzzing

docker run \
    -it \
    --rm \
    --cap-add SYS_PTRACE \
    -e FUZZING_ENGINE=aflgo \
    -e SANITIZER=address \
    -e PROJECT=hw-fuzzing \
    -e COMMIT=master \
    -e FUZZER= \
    --name master \
    -v $(OSS)/build/out/hw-fuzzing/master:/out \
    -v $(OSS)/build/work/hw-fuzzing/master:/work \
    -v $(HW_FUZZING)/scripts:/scripts \
    -t gcr.io/oss-fuzz/hw-fuzzing \
    bash
