CC := verilator
CFLAGS := -Wno-fatal -O2
OBJ_DIR := model

sim: $(DUT)
	./$(OBJ_DIR)/Vaes_128 $(INPUT)

$(DUT): V$(DUT).mk
	make -C $(OBJ_DIR) -f $^

V$(DUT).mk: $(SRCS) $(TB)
	verilator $(CFLAGS) -LDFLAGS $(LIBS) \
		--top-module $(DUT) \
		--Mdir $(OBJ_DIR) \
		--cc $(SRCS) \
		--exe $(TB);

.PHONY: sim clean

clean:
	@rm -rf $(OBJ_DIR)
