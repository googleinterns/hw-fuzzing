#!/bin/bash -eux
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

DOCKER_REPO="hw-fuzzing"
BASE_IMAGE_TAG="base-image"
CLANG_IMAGE_TAG="base-clang-11.0.0"
VERILATOR_IMAGE_TAG="base-verilator"
SIM_IMAGE_TAG="base-sim"
AFL_IMAGE_TAG="base-afl"
AFL_TERM_ON_CRASH_IMAGE_TAG="base-afl-term-on-crash"

if [ -z ${HW_FUZZING+x} ]; then
  echo "ERROR: Set HW_FUZZING path and try again."
else
  # Only (re)build these if they don't exist since they take a long time.
  docker inspect $DOCKER_REPO/$BASE_IMAGE_TAG >/dev/null 2>&1 || \
    docker build --pull -t $DOCKER_REPO/$BASE_IMAGE_TAG \
    $HW_FUZZING/infra/$BASE_IMAGE_TAG
  docker inspect $DOCKER_REPO/$CLANG_IMAGE_TAG >/dev/null 2>&1 || \
    docker build -t $DOCKER_REPO/$CLANG_IMAGE_TAG \
    $HW_FUZZING/infra/$CLANG_IMAGE_TAG
  docker inspect $DOCKER_REPO/$VERILATOR_IMAGE_TAG >/dev/null 2>&1 || \
    docker build -t $DOCKER_REPO/$VERILATOR_IMAGE_TAG \
    $HW_FUZZING/infra/$VERILATOR_IMAGE_TAG

  # (Re)Build all fuzzer/sim images (requires above to exist).
  docker build -t $DOCKER_REPO/$SIM_IMAGE_TAG $HW_FUZZING/infra/$SIM_IMAGE_TAG
  docker build -t $DOCKER_REPO/$AFL_IMAGE_TAG $HW_FUZZING/infra/$AFL_IMAGE_TAG
  docker build -t $DOCKER_REPO/$AFL_TERM_ON_CRASH_IMAGE_TAG \
    --build-arg AFL_REPO_URL="https://github.com/timothytrippel/AFL.git" \
    $HW_FUZZING/infra/$AFL_IMAGE_TAG
fi
