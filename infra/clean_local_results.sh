#!/bin/bash -eu
# Copyright 2021 Timothy Trippel
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

# Cleanup local build/fuzzing results
for SOC in $(ls hw/); do
  for DUT in $(ls hw/$SOC/); do
    if [ -d hw/$SOC/$DUT ]; then
      if [[ $DUT != "ot_template" ]]; then
        echo "Cleaning up build/fuzzing files in: $DUT ..."
        pushd hw/$SOC/$DUT >/dev/null
        rm -rf bin
        rm -rf build
        rm -rf model
        rm -rf logs
        rm -rf out
        rm -f *.vcd
        rm -f *.xml
        rm -f *.dat
        rm -rf tb/cocotb/*/__pycache__
        if [ -d seed_descriptions ]; then rm -rf seeds; fi
        popd >/dev/null
      fi
      if [[ $SOC == "other" && $DUT == "lock" ]]; then
        pushd hw/$SOC/$DUT >/dev/null
        rm -rf hdl_generator/locksmith/target
        rm -f hdl_generator/locksmith/Cargo.lock
        popd >/dev/null
      fi
      if [[ $SOC == "opentitan" ]]; then
        pushd hw/$SOC/$DUT >/dev/null
        rm -f Makefile
        popd >/dev/null
      fi
      if [[ $SOC == "rfuzz" ]]; then
        pushd hw/$SOC/$DUT >/dev/null
        rm -rf hdl
        rm -rf hdl_generator
        rm -rf tb
        rm -f Makefile
        popd >/dev/null
      fi

    fi
  done
done

# Cleanup Docker containers/image layers
docker ps -a -q | xargs -I {} docker rm {}
docker images -q -f dangling=true | xargs -I {} docker rmi -f {}
docker volume ls -qf dangling=true | xargs -I {} docker volume rm {}
echo "Done."
