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
# Directories
################################################################################
SCRIPTS     ?= ../../scripts
HDL_DIR     ?= hdl
TB_SRCS_DIR ?= src
TB_INC_DIR  ?= include
MODEL_DIR   ?= model
BUILD_DIR   ?= .
BIN_DIR     ?= .
export TB_SRCS_DIR
export TB_INC_DIR
export MODEL_DIR
export BUILD_DIR
export BIN_DIR

################################################################################
# Sources/Inputs
################################################################################
TB    = $(wildcard $(TB_SRCS_DIR)/*.cpp)
HDL   = $(wildcard $(HDL_DIR)/*.v)
MODEL = $(wildcard $(MODEL_DIR)/*.cpp)
INPUT = afl_in/seed.tf
export TB

################################################################################
# Verilator module prefix
################################################################################
VM_PREFIX = V$(DUT)
export VM_PREFIX

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
all: verilate exe seed sim

verilate: $(HDL)
	$(VERILATOR_ROOT)/bin/verilator $(VFLAGS) $(HDL)

$(BIN_DIR)/$(VM_PREFIX): $(MODEL) $(TB)
	make -f ../exe.mk

.PHONY: \
	clean-exe \
	clean-vlt \
	clean \
	cleanall \
	coverage \
	sim \
	exe \
	seed \
	afl_in_dir \
	afl_out_dir

coverage:
	verilator_coverage --annotate logs/annotated logs/coverage.dat

sim: $(BIN_DIR)/$(VM_PREFIX)
	@if [ ! -f $(INPUT) ]; then \
		echo "ERROR: run \"make seed\" first."; \
		exit 1; \
	else \
		./$(VM_PREFIX) $(INPUT) $(VM_PREFIX).vcd; \
	fi;

exe: $(BIN_DIR)/$(VM_PREFIX)

seed: afl_in_dir afl_out_dir
	python3 gen_seed.py $(INPUT) $(NUM_TESTS)

afl_in_dir:
	@echo "Creating dir for AFL input files..."; \
	mkdir -p afl_in;

afl_out_dir:
	@echo "Creating dir for AFL output files..."; \
	mkdir -p afl_out;

clean-exe:
	rm -rf logs
	rm -f $(BUILD_DIR)/*.o
	rm -f $(BUILD_DIR)/*.d
	rm -f $(BUILD_DIR)/*.bc
	rm -f $(BUILD_DIR)/*.txt
	rm -f $(VM_PREFIX)

clean-vlt:
	rm -rf $(MODEL_DIR)

clean: clean-exe clean-vlt

cleanall: clean
	rm -rf afl_*
