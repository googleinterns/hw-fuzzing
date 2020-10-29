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

DOCKER_REPO_BASENAME="hw-fuzzing"

if [ -z ${HW_FUZZING+x} ]; then
  echo "ERROR: Set HW_FUZZING path and try again."
else
  # Only rebuild these when prompted since they take a long time to build
  # TODO(ttrippel): check if they exist first, and build them if they don't
  if [[ ${1-} == "--all" ]]; then
    docker build --pull -t $DOCKER_REPO_BASENAME/base-image \
      $HW_FUZZING/infra/base-image
    docker build -t $DOCKER_REPO_BASENAME/base-clang-10.0.0 \
      $HW_FUZZING/infra/base-clang-10.0.0
    docker build -t $DOCKER_REPO_BASENAME/base-verilator \
      $HW_FUZZING/infra/base-verilator
  fi

  # Build all fuzzer/sim images (requires above to exist)
  docker build -t $DOCKER_REPO_BASENAME/base-sim $HW_FUZZING/infra/base-sim
  docker build -t $DOCKER_REPO_BASENAME/base-afl $HW_FUZZING/infra/base-afl
  docker build -t $DOCKER_REPO_BASENAME/base-afl-term-on-crash \
    --build-arg AFL_REPO_URL="https://github.com/timothytrippel/AFL.git" \
    $HW_FUZZING/infra/base-afl
fi
