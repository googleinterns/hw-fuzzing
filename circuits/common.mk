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
HDL_DIR                   ?= hdl
TB_DIR                    := tb/vlt
export TB_SRCS_DIR        := $(TB_DIR)/src
export TB_INCS_DIR        := $(TB_DIR)/include
export SHARED_TB_SRCS_DIR := ../tb/src
export SHARED_TB_INCS_DIR := ../tb/include
export MODEL_DIR          := model
export BUILD_DIR          := build
export BIN_DIR            := bin

################################################################################
# Sources/Inputs
################################################################################
export HDL            := $(wildcard $(HDL_DIR)/*.v)
export TB_SRCS        := $(wildcard $(TB_SRCS_DIR)/*.cpp)
export SHARED_TB_SRCS := $(wildcard $(SHARED_TB_SRCS_DIR)/*.cpp)
MODEL_SRCS             = $(HDL:$(HDL_DIR)/%.v=$(MODEL_DIR)/V%.cpp)

################################################################################
# Verilator module prefix
################################################################################
export VM_PREFIX = V$(CIRCUIT)

################################################################################
# Verilator flags
################################################################################
VFLAGS += \
	-Wno-fatal \
	--top-module $(CIRCUIT) \
	--Mdir $(MODEL_DIR) \
	--cc \
	--compiler clang

ifndef DISABLE_VCD_TRACING
	VFLAGS += --trace
endif

################################################################################
# Compilation rules
################################################################################
$(BIN_DIR)/$(VM_PREFIX): $(MODEL_SRCS) $(TB_SRCS) $(SHARED_TB_SRCS)
	@mkdir -p $(BUILD_DIR); \
	mkdir -p $(BIN_DIR); \
	make -f ../exe.mk

$(MODEL_DIR)/V%.cpp: $(HDL_DIR)/%.v
	$(VERILATOR_ROOT)/bin/verilator $(VFLAGS) $(HDL)

################################################################################
# Utility targets
################################################################################
.PHONY: clean cocotb sim

cocotb: $(HDL)
	make -C $(TB_DIR)

sim: $(BIN_DIR)/$(VM_PREFIX)
	./$(BIN_DIR)/$(VM_PREFIX) seeds/$(SEED)

clean:
	@rm -rf $(BIN_DIR)
	@rm -rf $(BUILD_DIR)
	@rm -rf $(MODEL_DIR)
	@rm -f *.vcd
	@rm -rf __pycache__
	@rm -rf tb/cocotb/$(BUILD_DIR)
	@rm -rf tb/cocotb/__pycache__
	@rm -f tb/cocotb/results.xml
	@rm -f tb/cocotb/coverage.dat
