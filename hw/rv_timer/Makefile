# TODO(ttrippel): include license header

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
	../../../opentitan/hw/ip/prim/rtl \
	../../../opentitan/hw/ip/tlul/rtl \
	../../../opentitan/hw/ip/$(TOPLEVEL)/rtl
export HDL := \
	../../../opentitan/hw/top_earlgrey/rtl/top_pkg.sv \
	../../../opentitan/hw/ip/tlul/rtl/tlul_pkg.sv \
	../../../opentitan/hw/ip/$(TOPLEVEL)/rtl/rv_timer_reg_pkg.sv \
	hdl/rv_timer.sv
	#../../../opentitan/hw/ip/$(TOPLEVEL)/rtl/rv_timer.sv
export SHARED_TB_SRCS := \
	verilator_tb.cpp \
	stdin_fuzz_tb.cpp \
	tlul_host_tb.cpp \
	ot_ip_fuzz_tb.cpp

################################################################################
# Verilator Flags (optional)
################################################################################
export VFLAGS := --assert -UVERILATOR

################################################################################
# Include common build targets
################################################################################
include ../common.mk

