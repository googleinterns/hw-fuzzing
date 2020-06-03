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

SCRIPTS_DIR := ../../scripts
SRCS_DIR    := ../../third_party/aes_128

SRCS  := $(wildcard $(SRCS_DIR)/*.v)
TB    := aes_128_test.cpp
DUT   := aes_128
LIBS  := -lcryptopp
INPUT := afl_in/seed.tf

# Default number of seed tests (encryptions)
ifndef
	NUM_TESTS := 5
endif

include ../common.mk

seed: afl_in_dir afl_out_dir
	python3 $(SCRIPTS_DIR)/gen_aes_seed_tf.py $(INPUT) $(NUM_TESTS)

afl_in_dir:
	@echo "Creating dir for AFL input files..."; \
	mkdir -p afl_in;

afl_out_dir:
	@echo "Creating dir for AFL output files..."; \
	mkdir -p afl_out;
