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
CXX       = clang++
DUT_CXX   = $(CXX)
TB_CXX    = $(CXX)
VLTRT_CXX = $(CXX)
LINK      = $(CXX)

################################################################################
# Preprocessor flags
################################################################################
include $(MODEL_DIR)/Vtop_classes.mk

# Set component specific flags to default CXXFLAGS
DUT_CXXFLAGS   = $(CXXFLAGS)
TB_CXXFLAGS    = $(CXXFLAGS)
VLTRT_CXXFLAGS = $(CXXFLAGS)

# Compiler flags to use to turn off unused and generated code warnings,
# such as -Wno-div-by-zero
CFG_CXXFLAGS_NO_UNUSED = \
	-Wno-sign-compare \
	-Wno-uninitialized \
	-Wno-unused-parameter \
	-Wno-unused-variable \
	-Wno-shadow

CPPFLAGS += \
	-I../.. \
	-I$(MODEL_DIR) \
	-I$(VERILATOR_ROOT)/include \
	-I$(VERILATOR_ROOT)/include/vltstd \
	-DVM_COVERAGE=$(VM_COVERAGE) \
	-DVM_TRACE=$(VM_TRACE) \
	$(CFG_CXXFLAGS_NO_UNUSED) \

################################################################################
# Source paths
################################################################################
VPATH += $(SHARED_TB_SRCS_DIR)
VPATH += $(TB_SRCS_DIR)
VPATH += $(MODEL_DIR)
VPATH += $(VERILATOR_ROOT)/include
VPATH += $(VERILATOR_ROOT)/include/vltstd

################################################################################
# Optimization control (modified from VLT default to isolate TB, DUT, and VLTRT)
################################################################################
DUT_OPT   = -O3
TB_OPT    = -O3
VLTRT_OPT = -O3

################################################################################
# DUT/Verilator-Runtime/Testbench classes
################################################################################
DUT_CLASSES   += $(VM_CLASSES_FAST)
VLTRT_CLASSES += $(VM_CLASSES_SLOW) \
								 $(VM_GLOBAL_FAST) \
								 $(VM_GLOBAL_SLOW) \
								 $(VM_SUPPORT_FAST) \
								 $(VM_SUPPORT_SLOW)

################################################################################
# Object file lists
################################################################################
DUT_OBJS    = $(addprefix $(BUILD_DIR)/, $(addsuffix .o, $(DUT_CLASSES)))
VLTRT_OBJS  = $(addprefix $(BUILD_DIR)/, $(addsuffix .o, $(VLTRT_CLASSES)))
TB_OBJS     = $(TB_SRCS:$(TB_SRCS_DIR)/%.cpp=$(BUILD_DIR)/%.o)
TB_OBJS    += $(SHARED_TB_SRCS:$(SHARED_TB_SRCS_DIR)/%.cpp=$(BUILD_DIR)/%.o)
ALL_OBJS    = $(DUT_OBJS) $(VLTRT_OBJS) $(TB_OBJS)

################################################################################
# Linking rules
################################################################################
$(BIN_DIR)/$(TOPLEVEL): $(ALL_OBJS)
	$(LINK) $(LDFLAGS) $^ $(LDLIBS) -o $@

################################################################################
# Compilation rules
################################################################################
# DUT Model
$(DUT_OBJS): $(BUILD_DIR)/%.o: %.cpp
	$(DUT_CXX) $(DUT_CXXFLAGS) $(CPPFLAGS) $(DUT_OPT) -c -o $@ $<

# Testbench code (don't want to instrument this when fuzzing)
$(TB_OBJS): $(BUILD_DIR)/%.o: %.cpp
	$(TB_CXX) $(TB_CXXFLAGS) $(CPPFLAGS) $(TB_OPT) -c -o $@ $<

# Verilator runtime code (don't want to instrument this when fuzzing)
$(VLTRT_OBJS): $(BUILD_DIR)/%.o: %.cpp
	$(VLTRT_CXX) $(VLTRT_CXXFLAGS) $(CPPFLAGS) $(VLTRT_OPT) -c -o $@ $<

.PHONY: debug-make

################################################################################
# Debugging
################################################################################
debug-make:
	@echo
	@echo "----------------------------------------------------------------------"
	@echo "Generic compiler configurations:"
	@echo "----------------------------------------------------------------------"
	@echo CXX:      $(CXX)
	@echo LINK:     $(LINK)
	@echo CXXFLAGS: $(CXXFLAGS)
	@echo CPPFLAGS: $(CPPFLAGS)
	@echo LDFLAGS:  $(LDFLAGS)
	@echo LDLIBS:   $(LDLIBS)
	@echo VPATH:    $(VPATH)
	@echo "----------------------------------------------------------------------"
	@echo "Verilator generated classes:"
	@echo "----------------------------------------------------------------------"
	@echo VM_CLASSES_FAST: $(VM_CLASSES_FAST)
	@echo VM_CLASSES_SLOW: $(VM_CLASSES_SLOW)
	@echo VM_SUPPORT_FAST: $(VM_SUPPORT_FAST)
	@echo VM_SUPPORT_SLOW: $(VM_SUPPORT_SLOW)
	@echo VM_GLOBAL_FAST:  $(VM_GLOBAL_FAST)
	@echo VM_GLOBAL_SLOW:  $(VM_GLOBAL_SLOW)
	@echo "----------------------------------------------------------------------"
	@echo "User provided classes:"
	@echo "----------------------------------------------------------------------"
	@echo VK_USER_OBJS: $(VK_USER_OBJS)
	@echo "----------------------------------------------------------------------"
	@echo "All object files:"
	@echo "----------------------------------------------------------------------"
	@echo ALL_OBJS: $(ALL_OBJS)
	@echo "----------------------------------------------------------------------"
	@echo "DUT compiler configurations:"
	@echo "----------------------------------------------------------------------"
	@echo DUT_CXX:      $(DUT_CXX)
	@echo DUT_CXXFLAGS: $(DUT_CXXFLAGS)
	@echo DUT_OPT:      $(DUT_OPT)
	@echo "----------------------------------------------------------------------"
	@echo "TB compiler configurations:"
	@echo "----------------------------------------------------------------------"
	@echo TB_CXX:      $(TB_CXX)
	@echo TB_CXXFLAGS: $(TB_CXXFLAGS)
	@echo TB_OPT:      $(TB_OPT)
	@echo "----------------------------------------------------------------------"
	@echo "Verilator Runtime compiler configurations:"
	@echo "----------------------------------------------------------------------"
	@echo VLTRT_CXX:      $(VLTRT_CXX)
	@echo VLTRT_CXXFLAGS: $(VLTRT_CXXFLAGS)
	@echo VLTRT_OPT:      $(VLTRT_OPT)
	@echo
