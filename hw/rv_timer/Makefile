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

################################################################################
# Circuit specific configs
################################################################################
export TOPLEVEL      := rv_timer
export TOPLEVEL_LANG := verilog
export TB_TYPE       ?= cpp
export TB            ?= afl
export CPPFLAGS      := -std=c++11
export LDFLAGS       :=
export LDLIBS        :=
export SEED          ?= afl_seed.1.tf

################################################################################
# Simulation Environment Vars
################################################################################

################################################################################
# HDL/TB
################################################################################
export HDL_INC_DIRS := \
	../tb/hdl \
	../../../opentitan/hw/ip/prim/rtl \
	../../../opentitan/hw/ip/tlul/rtl \
	../../../opentitan/hw/ip/$(TOPLEVEL)/rtl
export HDL := \
	../../../opentitan/hw/top_earlgrey/rtl/top_pkg.sv \
	../../../opentitan/hw/ip/tlul/rtl/tlul_pkg.sv \
	../../../opentitan/hw/ip/$(TOPLEVEL)/rtl/$(TOPLEVEL)_reg_pkg.sv \
	hdl/rv_timer.sv
export SHARED_TB_SRCS := \
	verilator_tb.cpp \
	stdin_fuzz_tb.cpp \
	tlul_host_tb.cpp \
	ot_ip_fuzz_tb.cpp

################################################################################
# Verilator Flags (optional)
################################################################################
export VFLAGS := --assert

################################################################################
# Include common build targets
################################################################################
include ../common.mk

