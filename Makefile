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

SHELL := /bin/bash

# Infrastructure
build-infra:
	infra/build_infra.sh

clean-infra:
	infra/cleanup_infra.sh

clean-fuzz-imgs:
	infra/cleanup_fuzzing_images.sh

rebuild-infra:
	infra/cleanup_infra.sh; infra/build_infra.sh

# Fuzzing locally
fuzz-ot-%: hw/opentitan/%/cpp_afl.hjson
	python3 infra/hwfp/hwfp/fuzz.py $<

fuzz-other-%: hw/other/%/cpp_afl.hjson
	python3 infra/hwfp/hwfp/fuzz.py $<

fuzz-rfuzz-%: hw/rfuzz/%/cpp_afl.hjson
	python3 infra/hwfp/hwfp/fuzz.py $<

# Synchronize GCS experiment data locally
sync-data:
	python3 infra/hwfp/hwfp/pull_data_from_gcs.py

# Cleanup local fuzzing build/results
clean:
	@for CORE in $(wildcard hw/*); do \
		if [[ $$CORE != "hw/ot_template" ]]; then \
			echo "Cleaning up fuzzing files in: $$CORE ..."; \
			pushd $$CORE >/dev/null; \
			rm -rf bin; \
			rm -rf build; \
			rm -rf model; \
			rm -rf logs; \
			rm -rf out; \
			rm -f *.vcd; \
			rm -f *.xml; \
			rm -f *.dat; \
			rm -rf tb/cocotb/*/__pycache__; \
			if [ -d seed_descriptions ]; then rm -rf seeds; fi; \
			popd >/dev/null; \
		fi; \
		if [[ $$CORE == "hw/lock" ]]; then \
			pushd $$CORE >/dev/null; \
			rm -rf hdl_generator/locksmith/target; \
			rm -f hdl_generator/locksmith/Cargo.lock; \
			popd >/dev/null; \
		fi; \
	done; \
  docker ps -a -q | xargs -I {} docker rm {}; \
  docker images -q -f dangling=true | xargs -I {} docker rmi -f {}; \
  docker volume ls -qf dangling=true | xargs -I {} docker volume rm {}; \
	echo "Done."

.PHONY: \
	build_infra \
	clean_infra \
	rebuild-infra
