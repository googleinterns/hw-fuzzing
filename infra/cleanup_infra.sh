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

DOCKER_REPO="hw-fuzzing"

# Remove all DUT Docker images
if [ -z ${HW_FUZZING+x} ]; then
  echo "ERROR: Set HW_FUZZING path and try again."
else

  # Remove all fuzzing images
  source $HW_FUZZING/infra/cleanup_fuzzing_images.sh

  # Remove all fuzzer/sim images
  docker rmi -f $DOCKER_REPO/base-afl-term-on-crash:latest
  docker rmi -f $DOCKER_REPO/base-afl:latest
  docker rmi -f $DOCKER_REPO/base-sim:latest

  # Only remove these when prompted since they take a long time to build
  if [[ ${1-} == "--all" ]]; then
    docker rmi -f $DOCKER_REPO/base-verilator:latest
    docker rmi -f $DOCKER_REPO/base-clang-11.0.0:latest
    docker rmi -f $DOCKER_REPO/base-image:latest
    docker rmi -f ubuntu:18.04
  fi

  # Cleanup Docker containers/image layers
  docker ps -a -q | xargs -I {} docker rm {}
  docker images -q -f dangling=true | xargs -I {} docker rmi -f {}
  docker volume ls -qf dangling=true | xargs -I {} docker volume rm {}
fi
