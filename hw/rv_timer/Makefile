# TODO(ttrippel): include license header

################################################################################
# Circuit specific configs
################################################################################
export TOPLEVEL      := rv_timer
export TOPLEVEL_LANG := verilog
export TB_TYPE       ?= cocotb
export TB            ?= afl
export CPPFLAGS      := -std=c++11
export LDFLAGS       :=
export LDLIBS        :=
export SEED          := afl_seed.0.tf

################################################################################
# Simulation Environment Vars
################################################################################
export INPUT_WIDTH ?= 8

################################################################################
# HDL Directories
################################################################################
export HDL_INC_DIRS := \
	../../../opentitan/hw/ip/prim/rtl \
	../../../opentitan/hw/ip/tlul/rtl \
	../../../opentitan/hw/ip/$(TOPLEVEL)/rtl
export HDL := \
	../../../opentitan/hw/top_earlgrey/rtl/top_pkg.sv \
	../../../opentitan/hw/ip/tlul/rtl/tlul_pkg.sv \
	../../../opentitan/hw/ip/$(TOPLEVEL)/rtl/rv_timer_reg_pkg.sv \
	../../../opentitan/hw/ip/$(TOPLEVEL)/rtl/rv_timer.sv

################################################################################
# Verilator Flags (optional)
################################################################################
export VFLAGS := -DVERILATOR

################################################################################
# Include common build targets
################################################################################
include ../common.mk

