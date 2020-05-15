CC      := verilator
CFLAGS  := -Wno-fatal -O2
OBJ_DIR := model

all: $(OBJ_DIR)/V$(DUT)
	./$^ $(INPUT) $(DUT).vcd

$(OBJ_DIR)/V$(DUT): V$(DUT).mk
	make -C $(OBJ_DIR) -f $^

V$(DUT).mk: $(SRCS) $(TB)
	verilator $(CFLAGS) -LDFLAGS $(LIBS) \
		--top-module $(DUT) \
		--Mdir $(OBJ_DIR) \
		--trace \
		--cc $(SRCS) \
		--exe $(TB)

.PHONY: all clean

clean:
	rm -rf $(OBJ_DIR)
	rm -rf logs
