#!/bin/bash -eu
# Copyright 2020 Timothy Trippel
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

# Remove all DUT Docker images
GCP_PROJECT_ID=$(gcloud config get-value project)
FUZZERS="afl-term-on-crash afl sim"
for DUT in aes lock rv_timer; do
  for FUZZER in $FUZZERS; do
    FUZZER_REGEX="gcr.io/$GCP_PROJECT_ID/$FUZZER-$DUT"
    docker images | grep $FUZZER_REGEX | awk '{print $3}' | \
      xargs docker rmi -f | >/dev/null
  done
done

# Cleanup Docker containers/image layers
docker ps -a -q | xargs -I {} docker rm {}
docker images -q -f dangling=true | xargs -I {} docker rmi -f {}
docker volume ls -qf dangling=true | xargs -I {} docker volume rm {}
