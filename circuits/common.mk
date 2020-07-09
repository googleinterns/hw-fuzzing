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
SCRIPTS           ?= ../../scripts
HDL_DIR           ?= hdl
TB_SRCS_DIR       ?= src
TB_INC_DIR        ?= include
MODEL_DIR         ?= model
BUILD_DIR         ?= build
BIN_DIR           ?= bin
FUZZER_INPUT_DIR  ?= afl_in
FUZZER_OUTPUT_DIR ?= afl_out
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
INPUT = $(FUZZER_INPUT_DIR)/seed
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
	--cc

ifdef DISABLE_VCD_TRACING
	VLT_VCD_TRACING :=
else
	VLT_VCD_TRACING := --trace
endif

################################################################################
# Compilation rules
################################################################################
all: verilate exe seed sim

verilate: $(HDL)
	$(VERILATOR_ROOT)/bin/verilator $(VFLAGS) $(VLT_VCD_TRACING) $(HDL)

$(BIN_DIR)/$(VM_PREFIX): $(MODEL) $(TB)
	@mkdir -p $(BUILD_DIR); \
	mkdir -p $(BIN_DIR); \
	make -f ../exe.mk

.PHONY: \
	clean-sim \
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
	./$(BIN_DIR)/$(VM_PREFIX) $(INPUT).0.tf; \

exe: $(BIN_DIR)/$(VM_PREFIX)

seed: afl_in_dir afl_out_dir
	python3 $(SCRIPTS)/gen_afl_seeds.py \
		$(FUZZER_INPUT_DIR)/seed \
		$(NUM_SEEDS) \
		$(NUM_TESTS_PER_SEED)

afl_in_dir:
	@echo "Creating dir for fuzzer input files..."; \
	mkdir -p $(FUZZER_INPUT_DIR);

afl_out_dir:
	@echo "Creating dir for fuzzer output files..."; \
	mkdir -p $(FUZZER_OUTPUT_DIR);

clean-sim:
	rm -rf logs
	rm -f *.vcd
	rm -rf $(FUZZER_INPUT_DIR)
	rm -rf $(FUZZER_OUTPUT_DIR)
	rm -rf __pycache__

clean-exe:
	rm -rf $(BIN_DIR)
	rm -rf $(BIN_DIR).*
	rm -rf $(BUILD_DIR)
	rm -rf $(BUILD_DIR).*

clean-vlt:
	rm -rf $(MODEL_DIR)

clean: clean-exe clean-vlt

cleanall: clean-sim clean
