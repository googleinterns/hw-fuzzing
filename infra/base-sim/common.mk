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

SHELL := /bin/bash

################################################################################
# Directories
################################################################################
export TB_DIR := tb/$(TB_TYPE)/$(TB)
ifeq ($(TB_TYPE), cocotb)
export TB_DIR             := $(shell cocotb-config --share)/lib/verilator
export SHARED_TB_SRCS_DIR :=
else
export SHARED_TB_SRCS_DIR := /src/hw/tb/$(TB_TYPE)/src
endif
export MODEL_DIR := model
export BUILD_DIR := build
export BIN_DIR   := bin
export SCRIPTS   ?= ./../scripts

################################################################################
# Sources/Inputs
################################################################################
ifeq ($(TB_TYPE), cocotb)
export TB_SRCS := $(shell cocotb-config --share)/lib/verilator/verilator.cpp
export SHARED_TB_SRCS :=
TB_MODULE := tb.$(TB_TYPE).$(TB).$(TOPLEVEL)_tb
else
export TB_SRCS        := $(wildcard $(TB_DIR)/*.cpp)
export SHARED_TB_SRCS := $(addprefix $(SHARED_TB_SRCS_DIR)/, $(SHARED_TB_SRCS))
endif
MODEL_SRC := $(MODEL_DIR)/Vtop.cpp

################################################################################
# Verilator flags
################################################################################
VLT_TOPMODULE ?= $(TOPLEVEL)_tb
VFLAGS += \
	-Wno-fatal \
	--prefix Vtop \
	--Mdir $(MODEL_DIR) \
	--top-module $(VLT_TOPMODULE) \
	--cc \
	--compiler clang

# Other setting for cocotb support
ifeq ($(TB_TYPE), cocotb)
VFLAGS   += -DCOCOTB_SIM=1 --vpi --public-flat-rw
LDFLAGS  += -Wl,-rpath,$(shell cocotb-config --prefix)/cocotb/libs
LDFLAGS  += -L$(shell cocotb-config --prefix)/cocotb/libs
LDLIBS   += -lcocotbvpi_verilator -lgpi -lcocotb -lgpilog -lcocotbutils
CPPFLAGS += "-DVL_TIME_PRECISION_STR=1ps"
export COCOTB_REDUCED_LOG_FMT := 1
export COCOTB_LOG_LEVEL       := DEBUG
export LD_LIBRARY_PATH        := $(shell cocotb-config --prefix)/cocotb/libs
endif

ifdef HDL_INC_DIRS
VFLAGS += $(addprefix -I, $(HDL_INC_DIRS))
endif

ifdef ENABLE_COVERAGE_TRACING
VFLAGS += --coverage
endif

ifndef DISABLE_VCD_TRACING
VFLAGS += --trace
VFLAGS += -DUNPACK_TLUL
endif

################################################################################
# Compilation rules
################################################################################
$(BIN_DIR)/$(TOPLEVEL): $(MODEL_SRC) $(TB_SRCS) $(SHARED_TB_SRCS)
	$(SCRIPTS)/gen-seeds-from-yaml; \
	mkdir -p $(BUILD_DIR); \
	mkdir -p $(BIN_DIR); \
	$(MAKE) -f ../exe.mk debug-make; \
	$(MAKE) -f ../exe.mk

$(MODEL_SRC): $(HDL)
	$(VERILATOR_ROOT)/bin/verilator $(VFLAGS) $^

%.sv:
	$(shell fusesoc --cores-root=$(DUT_HDL_DIR) run --tool=verilator \
		--setup $(FUSESOC_LIBRARY):$(TOPLEVEL)) || true

################################################################################
# Utility targets
################################################################################
.PHONY: clean sim debug-make report-svas report-bbs

report-svas: $(HDL)
	@python3 $(HW)/hwfutils/hwfutils/report_svas.py $(HDL);

report-bbs: $(MODEL_SRC) $(TB_SRCS) $(SHARED_TB_SRCS)
	mkdir -p $(BUILD_DIR); \
	mkdir -p $(BIN_DIR); \
	$(MAKE) -f ../exe.mk bb-stats; \

ifeq ($(TB_TYPE), cocotb)
sim: $(BIN_DIR)/$(TOPLEVEL)
	MODULE=$(TB_MODULE) $< < seeds/$(SEED)
else
sim: $(BIN_DIR)/$(TOPLEVEL)
	$< < seeds/$(SEED)
endif

clean:
	@rm -rf $(BIN_DIR)
	@rm -rf $(BUILD_DIR)
	@rm -rf $(MODEL_DIR)
	@rm -f *.vcd
	@rm -f *.xml
	@rm -f *.dat
	@rm -rf tb/cocotb/*/__pycache__
	@if [ -d seed_descriptions ]; then rm -rf seeds; fi

################################################################################
# Debugging
################################################################################
debug-make::
	@echo
	@echo "----------------------------------------------------------------------"
	@echo "Toplevel Info:"
	@echo "----------------------------------------------------------------------"
	@echo TOPLEVEL:      $(TOPLEVEL)
	@echo TOPLEVEL_LANG: $(TOPLEVEL_LANG)
	@echo "----------------------------------------------------------------------"
	@echo "HDL:"
	@echo "----------------------------------------------------------------------"
	@echo HDL: $(HDL)
	@echo "----------------------------------------------------------------------"
	@echo "Testbench:"
	@echo "----------------------------------------------------------------------"
	@echo TB_DIR:         $(TB_DIR)
	@echo TB_SRCS:        $(TB_SRCS)
	@echo SHARED_TB_SRCS: $(SHARED_TB_SRCS)
	@echo "----------------------------------------------------------------------"
	@echo "Verilator Flags:"
	@echo "----------------------------------------------------------------------"
	@echo VFLAGS: $(VFLAGS)
	@echo "----------------------------------------------------------------------"
	@echo "cocotb/Verilator Configs:"
	@echo "----------------------------------------------------------------------"
	@echo CPPFLAGS:        $(CPPFLAGS)
	@echo LDFLAGS:         $(LDFLAGS)
	@echo LDLIBS:          $(LDLIBS)
	@echo LD_LIBRARY_PATH: $(LD_LIBRARY_PATH)
	@echo
