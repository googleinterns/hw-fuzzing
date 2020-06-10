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
# Core specific configs
################################################################################
export DUT      := double_counter
export LIBS     :=
export CPPFLAGS :=

################################################################################
# Default number of seed tests (counter increments)
################################################################################
ifndef
	NUM_TESTS := 1000
endif

################################################################################
# Directories
################################################################################
SCRIPTS            ?= ../../scripts
HDL_DIR            := hdl
export TB_SRCS_DIR := src
export TB_INC_DIR  := include
export MODEL_DIR   := model

########## DO NOT MODIFY BELOW ##########

################################################################################
# Include common build targets
################################################################################
include ../common.mk
