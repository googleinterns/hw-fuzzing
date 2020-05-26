CC      := verilator
CFLAGS  := -Wno-fatal -O2
OBJ_DIR := model

ifndef COVERAGE
	VFLAGS := --top-module $(DUT) --Mdir $(OBJ_DIR) --trace --cc
else
	VFLAGS := --top-module $(DUT) --Mdir $(OBJ_DIR) --trace $(COVERAGE) --cc
endif

all: $(OBJ_DIR)/V$(DUT)
	./$^ $(INPUT) $(DUT).vcd

$(OBJ_DIR)/V$(DUT): V$(DUT).mk
	make -C $(OBJ_DIR) -f $^

V$(DUT).mk: $(SRCS) $(TB)
	verilator $(CFLAGS) -LDFLAGS $(LIBS) $(VFLAGS) $(SRCS) --exe $(TB)

.PHONY: all clean seed coverage

coverage:
	verilator_coverage --annotate logs/annotated logs/coverage.dat

clean:
	rm -rf $(OBJ_DIR)
	rm -rf logs
