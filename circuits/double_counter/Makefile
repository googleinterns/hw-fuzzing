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
export DUT       := double_counter
export LIBS      :=
export CPPFLAGS  := -std=c++11
export LINKFLAGS := -std=c++11

################################################################################
# Default number of seed tests (counter increments)
################################################################################
NUM_SEEDS ?= 1
NUM_TESTS_PER_SEED ?= 1

################################################################################
# Directories
################################################################################
#HDL_DIR := ../../third_party/$(DUT)# uncomment if third party IP block

########## DO NOT MODIFY BELOW ##########

################################################################################
# Include common build targets
################################################################################
include ../common.mk
