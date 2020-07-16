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

## Remove all fuzzing infrastructure Docker images
#docker rmi -f hw-fuzzing/base-aflgo-fork:latest
#docker rmi -f hw-fuzzing/base-aflgo:latest
#docker rmi -f hw-fuzzing/base-afl-fork:latest
#docker rmi -f hw-fuzzing/base-afl:latest
#docker rmi -f hw-fuzzing/base-clang-4.0.0:latest
#docker rmi -f hw-fuzzing/base-clang-10.0.0:latest
#docker rmi -f hw-fuzzing/base-verilator:latest
#docker rmi -f hw-fuzzing/base-image:latest

# Remove all circuit infrastructure Docker images
docker rmi -f hw-fuzzing/base-opentitan:latest

# Cleanup Docker containers
docker ps -a -q | xargs -I {} docker rm {};
docker images -q -f dangling=true | xargs -I {} docker rmi -f {};
docker volume ls -qf dangling=true | xargs -I {} docker volume rm {};
