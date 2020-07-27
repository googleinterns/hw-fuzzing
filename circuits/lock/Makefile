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
# Circuit specific configs
################################################################################
export CIRCUIT        := lock
export LIBS           :=
export CPPFLAGS       := -std=c++11
export LINKFLAGS      := -std=c++11
export SEED           := afl_seed.0.tf
NUM_LOCK_STATES       ?= 8
LOCK_COMP_WIDTH       ?= 8
BACKTRACK_PROBABILITY ?= 0

################################################################################
# Directories
################################################################################
#HDL_DIR := ../../third_party/$(CIRCUIT)# uncomment if third party IP block

################################################################################
# Include common build targets
################################################################################
include ../common.mk

################################################################################
# HDL generation/clean targets
################################################################################
.PHONY: clean-hdl

hdl: hdl_generator/src/main.rs
	@mkdir hdl; \
	cd hdl_generator; \
	cargo build; \
	cargo run -- \
		--states $(NUM_LOCK_STATES) \
		--width $(LOCK_COMP_WIDTH) \
		--backtrack $(BACKTRACK_PROBABILITY) > ../hdl/$(CIRCUIT).v; \
	cd ..

clean-hdl:
	rm -rf hdl
