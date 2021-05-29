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

ifndef DUT_HDL_DIR
$(error DUT_HDL_DIR is not set ... ABORTING.)
endif

################################################################################
# Circuit specific configs
################################################################################
export TOPLEVEL_LANG := verilog
export CPPFLAGS      += -std=c++11
export LDFLAGS       +=
export LDLIBS        :=

################################################################################
# FuseSoC Settings (for generated OpenTitan IP)
################################################################################
FUSESOC_LIBRARY := lowrisc:ip
FUSESOC_CORE    := lowrisc_ip_$(TOPLEVEL)_$(FUSESOC_VERSION)

################################################################################
# HDL/TB
################################################################################
export HDL_INC_DIRS := ../tb/hdl
export HDL := hdl/$(TOPLEVEL)_tb.sv

export SHARED_TB_SRCS := \
	verilator_tb.cpp \
	stdin_fuzz_tb.cpp \
	tlul_host_tb.cpp \
	ot_ip_fuzz_tb.cpp

ifndef DISABLE_VCD_TRACING
HDL += ../tb/hdl/tlul_inspect.sv
endif

################################################################################
# Verilator Flags (optional)
################################################################################
export VFLAGS := --assert
#export VFLAGS += -DINJECTED_BUG_CHECK

################################################################################
# Include common build targets
################################################################################
include ../common.mk
