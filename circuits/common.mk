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

################################################################################
# Sources/Inputs
################################################################################
export TB := $(wildcard $(TB_SRCS_DIR)/*.cpp)
HDL       := $(wildcard $(HDL_DIR)/*.v)
INPUT     := afl_in/seed.tf

################################################################################
# Verilator module prefix
################################################################################
export VM_PREFIX := V$(DUT)

################################################################################
# Verilator flags
################################################################################
VFLAGS := \
	-Wno-fatal \
	--top-module $(DUT) \
	--Mdir $(MODEL_DIR) \
	--trace \
	$(COVERAGE) \
	--cc

################################################################################
# Compilation rules
################################################################################
verilate: $(HDL) $(TB)
	$(VERILATOR_ROOT)/bin/verilator $(VFLAGS) $(HDL) --exe $(TB)

$(VM_PREFIX):
	make -f ../exe.mk

.PHONY: clean cleanall coverage sim exe seed afl_in_dir afl_out_dir

coverage:
	verilator_coverage --annotate logs/annotated logs/coverage.dat

sim: $(VM_PREFIX)
	@if [ ! -f $(INPUT) ]; then \
		echo "ERROR: run \"make seed\" first."; \
		exit 1; \
	else \
		./$(VM_PREFIX) $(INPUT) $(VM_PREFIX).vcd; \
	fi;

exe: $(VM_PREFIX)

seed: afl_in_dir afl_out_dir
	python3 gen_seed.py $(INPUT) $(NUM_TESTS)

afl_in_dir:
	@echo "Creating dir for AFL input files..."; \
	mkdir -p afl_in;

afl_out_dir:
	@echo "Creating dir for AFL output files..."; \
	mkdir -p afl_out;

clean:
	rm -rf $(MODEL_DIR)
	rm -rf logs
	rm -f *.o *.d *.bc *.txt
	rm -f $(TB_SRCS_DIR)/*.o $(TB_SRCS_DIR)/*.d
	rm -f $(VM_PREFIX)

cleanall: clean
	rm -rf afl_*
