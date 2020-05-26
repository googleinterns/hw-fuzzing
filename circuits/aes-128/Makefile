SCRIPTS_DIR := ../../scripts
SRCS_DIR    := ../../third_party/aes-128

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

seed: afl_in_dir
	python3 $(SCRIPTS_DIR)/gen_aes_seed_tf.py $(INPUT) $(NUM_TESTS)

afl_in_dir:
	@echo "Creating dir for AFL input files..."; \
	mkdir -p afl_in;
