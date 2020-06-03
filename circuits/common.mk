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
# Compiler/Linker
################################################################################
CXX = g++
LINK = g++

################################################################################
# Switches
################################################################################
# SystemC output mode?  0/1 (from --sc)
VM_SC = 0

################################################################################
# Preprocessor flags
################################################################################
# Compiler flags to use to turn off unused and generated code warnings,
# such as -Wno-div-by-zero
CFG_CXXFLAGS_NO_UNUSED = \
	-faligned-new \
	-fcf-protection=none \
	-Wno-sign-compare \
	-Wno-uninitialized \
	-Wno-unused-parameter \
	-Wno-unused-variable \
	-Wno-shadow

# Add -MMD -MP if you're using a recent version of GCC.
VK_CPPFLAGS_ALWAYS += \
	-MMD \
	-I$(TB_INC_DIR) \
	-I$(MODEL_DIR)\
	-I$(VERILATOR_ROOT)/include \
	-I$(VERILATOR_ROOT)/include/vltstd \
	-DVM_COVERAGE=$(VM_COVERAGE) \
	-DVM_SC=$(VM_SC) \
	-DVM_TRACE=$(VM_TRACE) \
	$(CFG_CXXFLAGS_NO_UNUSED) \

CPPFLAGS += $(VK_CPPFLAGS_WALL) $(VK_CPPFLAGS_ALWAYS)

################################################################################
# Source paths
################################################################################
VPATH += $(TB_SRCS_DIR)
VPATH += $(MODEL_DIR)
VPATH += $(VERILATOR_ROOT)/include
VPATH += $(VERILATOR_ROOT)/include/vltstd

################################################################################
# Optimization control
################################################################################
# See also the BENCHMARKING & OPTIMIZATION section of the manual.

# Optimization flags for non performance-critical/rarely executed code.
# No optimization by default, which improves compilation speed.
OPT_SLOW =
# Optimization for performance critical/hot code. Most time is spent in these
# routines. Optimizing by default for improved execution speed.
OPT_FAST = -Os
# Optimization applied to the common run-time library used by verilated models.
# For compatibility this is called OPT_GLOBAL even though it only applies to
# files in the run-time library. Normally there should be no need for the user
# to change this as the library is small, but can have significant speed impact.
OPT_GLOBAL = -Os

################################################################################
# Verilator/Testbench classes
################################################################################
include $(MODEL_DIR)/$(VM_PREFIX)_classes.mk

VM_FAST += $(VM_CLASSES_FAST) $(VM_SUPPORT_FAST)
VM_SLOW += $(VM_CLASSES_SLOW) $(VM_SUPPORT_SLOW)

# Note VM_GLOBAL_FAST and VM_GLOBAL_SLOW holds the files required from the
# run-time library. In practice everything is actually in VM_GLOBAL_FAST,
# but keeping the distinction for compatibility for now.
VM_GLOBAL += $(VM_GLOBAL_FAST) $(VM_GLOBAL_SLOW)

################################################################################
# Object file lists...
################################################################################
VK_FAST_OBJS   = $(addsuffix .o, $(VM_FAST))
VK_SLOW_OBJS   = $(addsuffix .o, $(VM_SLOW))
VK_GLOBAL_OBJS = $(addsuffix .o, $(VM_GLOBAL))
VK_USER_OBJS   = $(TB:.cpp=.o)

VK_ALL_OBJS = $(VK_USER_OBJS) $(VK_GLOBAL_OBJS) $(VK_FAST_OBJS) $(VK_SLOW_OBJS)

################################################################################
# Linking rules
################################################################################
$(VM_PREFIX): $(VK_ALL_OBJS)
	$(LINK) $^ $(LIBS) -o $@

################################################################################
# Compilation rules
################################################################################
# Anything not in $(VK_SLOW_OBJS) or $(VK_GLOBAL_OBJS), including verilated.o
# and user files passed on the Verilator command line use this rule.
%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(OPT_FAST) -c -o $@ $<

$(VK_SLOW_OBJS): %.o: %.cpp
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(OPT_SLOW) -c -o $@ $<

$(VK_GLOBAL_OBJS): %.o: %.cpp
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(OPT_GLOBAL) -c -o $@ $<

$(VK_USER_OBJS): %.o: %.cpp
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(OPT_FAST) -c -o $@ $<

.PHONY: debug-make

################################################################################
# Debugging
################################################################################
debug-make::
	@echo
	@echo CXXFLAGS: $(CXXFLAGS)
	@echo CPPFLAGS: $(CPPFLAGS)
	@echo OPT_FAST: $(OPT_FAST)
	@echo OPT_SLOW: $(OPT_SLOW)
	@echo VM_PREFIX:  $(VM_PREFIX)
	@echo VM_CLASSES_FAST: $(VM_CLASSES_FAST)
	@echo VM_CLASSES_SLOW: $(VM_CLASSES_SLOW)
	@echo VM_SUPPORT_FAST: $(VM_SUPPORT_FAST)
	@echo VM_SUPPORT_SLOW: $(VM_SUPPORT_SLOW)
	@echo VM_GLOBAL_FAST: $(VM_GLOBAL_FAST)
	@echo VM_GLOBAL_SLOW: $(VM_GLOBAL_SLOW)
	@echo VK_OBJS: $(VK_OBJS)
	@echo
