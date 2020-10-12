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

ifndef OPENTITAN_ROOT
$(error OPENTITAN_ROOT is not set ... ABORTING.)
endif

################################################################################
# Circuit specific configs
################################################################################
export TOPLEVEL      := aes
export TOPLEVEL_LANG := verilog
export TB_TYPE       ?= cpp
export TB            ?= afl
export CPPFLAGS      := -std=c++11
export LDFLAGS       :=
export LDLIBS        :=
export SEED          ?= auto_ctr_128bit_encrypt_1block.tf

################################################################################
# Simulation Environment Vars
################################################################################
# N/A

################################################################################
# FuseSoC Settings (for generated OpenTitan IP)
################################################################################
FUSESOC_VERSION  := 0.6
FUSESOC_CORE     := lowrisc_ip_$(TOPLEVEL)_$(FUSESOC_VERSION)
FUSESOC_GEN_PATH := build/$(FUSESOC_CORE)/default-verilator/generated/lowrisc

################################################################################
# HDL/TB
################################################################################
export HDL_INC_DIRS := ../tb/hdl
export HDL := \
	$(OPENTITAN_ROOT)/hw/top_earlgrey/rtl/top_pkg.sv \
	\
	$(OPENTITAN_ROOT)/hw/ip/prim/rtl/prim_intr_hw.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim/rtl/prim_subreg_arb.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim/rtl/prim_subreg_ext.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim/rtl/prim_subreg_shadow.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim/rtl/prim_subreg.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim/rtl/prim_alert_pkg.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim/rtl/prim_cipher_pkg.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim/rtl/prim_pulse_sync.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim/rtl/prim_lfsr.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim_generic/rtl/prim_generic_flop_2sync.sv \
	$(OPENTITAN_ROOT)/hw/ip/prim_generic/rtl/prim_generic_flop.sv \
	\
	$(FUSESOC_GEN_PATH)_prim_flop_2sync-impl_0/prim_flop_2sync.sv \
	$(FUSESOC_GEN_PATH)_prim_prim_pkg-impl_0.1/prim_pkg.sv \
	$(FUSESOC_GEN_PATH)_prim_flop-impl_0/prim_flop.sv \
	\
	../tb/hdl/prim_assert_hwfuzzing_macros.svh \
	../tb/hdl/prim_assert.sv \
	../tb/hdl/prim_alert_sender.sv \
	../tb/hdl/prim_diff_decode.sv \
	\
	$(OPENTITAN_ROOT)/hw/ip/tlul/rtl/tlul_pkg.sv \
	$(OPENTITAN_ROOT)/hw/ip/tlul/rtl/tlul_adapter_reg.sv \
	$(OPENTITAN_ROOT)/hw/ip/tlul/rtl/tlul_err.sv \
	\
	$(OPENTITAN_ROOT)/hw/ip/$(TOPLEVEL)/rtl/$(TOPLEVEL)_reg_pkg.sv \
	$(OPENTITAN_ROOT)/hw/ip/$(TOPLEVEL)/rtl/$(TOPLEVEL)_reg_top.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_pkg.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_sbox_canright_pkg.sv \
	\
	$(OPENTITAN_ROOT)/hw/ip/$(TOPLEVEL)/rtl/$(TOPLEVEL).sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_cipher_control.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_cipher_core.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_control.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_core.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_ctr.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_key_expand.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_mix_columns.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_mix_single_column.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_prng_clearing.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_prng_masking.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_reg_status.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_sbox.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_sbox_canright.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_sbox_canright_masked.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_sbox_canright_masked_noreuse.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_sbox_lut.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_shift_rows.sv \
	$(OPENTITAN_ROOT)/hw/ip/aes/rtl/aes_sub_bytes.sv \
	\
	hdl/$(TOPLEVEL)_tb.sv
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
