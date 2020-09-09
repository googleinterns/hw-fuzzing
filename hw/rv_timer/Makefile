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
# Directories
################################################################################
HDL_DIR := ../../../opentitan/hw/ip/$(TOPLEVEL)/rtl

################################################################################
# Include common build targets
################################################################################
include ../common.mk

