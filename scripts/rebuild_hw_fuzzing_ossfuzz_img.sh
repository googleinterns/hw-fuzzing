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

# TODO: Set path to OSS-Fuzz in .bashrc
#export OSS=/path/to/oss-fuzz

# Cleanup Docker containers
docker rmi -f gcr.io/oss-fuzz/hw-fuzzing:latest
docker ps -a -q | xargs -I {} docker rm {};
docker images -q -f dangling=true | xargs -I {} docker rmi -f {};
docker volume ls -qf dangling=true | xargs -I {} docker volume rm {};

# Cleanup output of OSS-Fuzz containers
sudo rm -rf $(OSS)/build/out/hw-fuzzing
sudo rm -rf $(OSS)/build/work/hw-fuzzing

# Rebuild the hw-fuzzing OSS-Fuzz Docker image
python $OSS/infra/helper.py build_image hw-fuzzing
