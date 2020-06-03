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

OBJ_DIR := model

ifndef COVERAGE
	VFLAGS := -Wno-fatal -O2 --top-module $(DUT) --Mdir $(OBJ_DIR) --trace --cc
else
	VFLAGS := -Wno-fatal -O2 --top-module $(DUT) --Mdir $(OBJ_DIR) --trace $(COVERAGE) --cc
endif

V$(DUT).mk: $(SRCS) $(TB)
	verilator $(VFLAGS) -CFLAGS -std=c++11 -LDFLAGS $(LIBS) $(SRCS) --exe $(TB)

.PHONY: clean coverage exe seed sim

coverage:
	verilator_coverage --annotate logs/annotated logs/coverage.dat

sim:
	./$(OBJ_DIR)/V$(DUT) $(INPUT) $(DUT).vcd

exe: V$(DUT).mk
	make -C $(OBJ_DIR) -f $^

clean:
	rm -rf $(OBJ_DIR)
	rm -rf logs
