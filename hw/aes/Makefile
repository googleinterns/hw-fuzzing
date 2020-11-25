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

ifndef DUT_HDL_DIR
$(error DUT_HDL_DIR is not set ... ABORTING.)
endif

################################################################################
# Circuit specific configs
################################################################################
export TOPLEVEL      := aes
export TOPLEVEL_LANG := verilog
export TB_TYPE       ?= cpp
export TB            ?= afl
export CPPFLAGS      += -std=c++11
export LDFLAGS       +=
export LDLIBS        :=
export SEED          ?= auto_ctr_128bit_encrypt_1block.hwf

################################################################################
# Simulation Environment Vars
################################################################################
# N/A

################################################################################
# FuseSoC Settings (for generated OpenTitan IP)
################################################################################
FUSESOC_VERSION  := 0.6
FUSESOC_LIBRARY  := lowrisc:ip
FUSESOC_CORE     := lowrisc_ip_$(TOPLEVEL)_$(FUSESOC_VERSION)
FUSESOC_GEN_PATH := build/$(FUSESOC_CORE)/default-verilator/generated/lowrisc

################################################################################
# HDL/TB
################################################################################
export HDL_INC_DIRS := ../tb/hdl
export HDL := \
	$(DUT_HDL_DIR)/hw/top_earlgrey/rtl/top_pkg.sv \
	\
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_alert_pkg.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_alert_sender.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_diff_decode.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_intr_hw.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_subreg_arb.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_subreg_ext.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_subreg_shadow.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_subreg.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_cipher_pkg.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_pulse_sync.sv \
	$(DUT_HDL_DIR)/hw/ip/prim/rtl/prim_lfsr.sv \
	$(DUT_HDL_DIR)/hw/ip/prim_generic/rtl/prim_generic_flop_2sync.sv \
	$(DUT_HDL_DIR)/hw/ip/prim_generic/rtl/prim_generic_flop.sv \
	\
	$(FUSESOC_GEN_PATH)_prim_flop_2sync-impl_0/prim_flop_2sync.sv \
	$(FUSESOC_GEN_PATH)_prim_prim_pkg-impl_0.1/prim_pkg.sv \
	$(FUSESOC_GEN_PATH)_prim_flop-impl_0/prim_flop.sv \
	\
	../tb/hdl/prim_assert_hwfuzzing_macros.svh \
	../tb/hdl/prim_assert.sv \
	\
	$(DUT_HDL_DIR)/hw/ip/tlul/rtl/tlul_pkg.sv \
	$(DUT_HDL_DIR)/hw/ip/tlul/rtl/tlul_adapter_reg.sv \
	$(DUT_HDL_DIR)/hw/ip/tlul/rtl/tlul_err.sv \
	\
	$(DUT_HDL_DIR)/hw/ip/$(TOPLEVEL)/rtl/$(TOPLEVEL)_reg_pkg.sv \
	$(DUT_HDL_DIR)/hw/ip/$(TOPLEVEL)/rtl/$(TOPLEVEL)_reg_top.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_pkg.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_sbox_canright_pkg.sv \
	\
	$(DUT_HDL_DIR)/hw/ip/$(TOPLEVEL)/rtl/$(TOPLEVEL).sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_cipher_control.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_cipher_core.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_control.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_core.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_ctr.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_key_expand.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_mix_columns.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_mix_single_column.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_prng_clearing.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_prng_masking.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_reg_status.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_sbox.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_sbox_canright.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_sbox_canright_masked.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_sbox_canright_masked_noreuse.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_sbox_lut.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_shift_rows.sv \
	$(DUT_HDL_DIR)/hw/ip/aes/rtl/aes_sub_bytes.sv \
	\
	hdl/$(TOPLEVEL)_tb.sv
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

################################################################################
# Include common build targets
################################################################################
include ../common.mk
