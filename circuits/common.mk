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
SCRIPTS            ?= ../../scripts
HDL_DIR            ?= hdl
TB_SRCS_DIR        ?= src
TB_INCS_DIR        ?= include
SHARED_TB_SRCS_DIR ?= ../testbench/src
SHARED_TB_INCS_DIR ?= ../testbench/include
MODEL_DIR          ?= model
BUILD_DIR          ?= build
BIN_DIR            ?= bin
FUZZER_INPUT_DIR   ?= in
FUZZER_OUTPUT_DIR  ?= out
export TB_SRCS_DIR
export TB_INCS_DIR
export SHARED_TB_SRCS_DIR
export SHARED_TB_INCS_DIR
export MODEL_DIR
export BUILD_DIR
export BIN_DIR

################################################################################
# Sources/Inputs
################################################################################
SHARED_TB ?= $(SHARED_TB_SRCS_DIR)/verilator_test.cpp
TB        ?= $(TB_SRCS_DIR)/$(CIRCUIT)_test.cpp
HDL        = $(wildcard $(HDL_DIR)/*.v)
MODEL      = $(wildcard $(MODEL_DIR)/*.cpp)
export SHARED_TB
export TB

################################################################################
# Verilator module prefix
################################################################################
VM_PREFIX = V$(CIRCUIT)
export VM_PREFIX

################################################################################
# Verilator flags
################################################################################
VFLAGS := \
	-Wno-fatal \
	--top-module $(CIRCUIT) \
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

verilate: $(HDL_DIR)
	$(VERILATOR_ROOT)/bin/verilator $(VFLAGS) $(VLT_VCD_TRACING) $(HDL)

$(BIN_DIR)/$(VM_PREFIX): $(MODEL) $(SHARED_TB) $(TB)
	@mkdir -p $(BUILD_DIR); \
	mkdir -p $(BIN_DIR); \
	make -f ../exe.mk

.PHONY: \
	clean-hdl \
	clean-sim \
	clean-exe \
	clean-vlt \
	clean \
	cleanall \
	coverage \
	hdl \
	sim \
	exe \
	seed

coverage:
	verilator_coverage --annotate logs/annotated logs/coverage.dat

sim: $(BIN_DIR)/$(VM_PREFIX)
	./$(BIN_DIR)/$(VM_PREFIX) $(FUZZER_INPUT_DIR)/$(SEED)

exe: $(BIN_DIR)/$(VM_PREFIX)

seed:
	@echo "Creating dir for fuzzer outputs ..."; \
	echo "Creating dir for fuzzer inputs ..."; \
	echo "Copying seeds to fuzzer input dir ..."; \
	cp -r seeds $(FUZZER_INPUT_DIR)

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

cleanall: clean-sim clean-hdl clean
