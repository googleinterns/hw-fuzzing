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
# Design Specific Configs
################################################################################
export TOPLEVEL      := lock
export TOPLEVEL_LANG := verilog
export TB_TYPE       ?= cpp
export TB            ?= afl
export CPPFLAGS      := -std=c++11
export LDFLAGS       :=
export LDLIBS        :=
export SEED          := afl_seed.0.tf

################################################################################
# Simulation Environment Vars
################################################################################
export NUM_LOCK_STATES ?= 4
export LOCK_COMP_WIDTH ?= 8

################################################################################
# HDL/TB
################################################################################
#export HDL_INC_DIRS :=
export HDL            := hdl/lock.v
export SHARED_TB_SRCS := verilator_tb.cpp

################################################################################
# Verilator Flags (optional)
################################################################################
#export VFLAGS :=

################################################################################
# Include common build targets
################################################################################
include ../common.mk
