// TODO(ttrippel): add license

#include "hw/tb/cpp/inc/ot_ip_fuzz_tb.h"

// Testbench needs to be global for sc_time_stamp()
OTIPFuzzTb* tb = NULL;

// needs to be defined so Verilog can call $time
double sc_time_stamp() { return tb->get_main_time(); }

int main(int argc, char** argv, char** env) {
  // Instantiate testbench
  tb = new OTIPFuzzTb(argc, argv);

  // Simulate the DUT
  tb->SimulateDUT();

  // Teardown
  delete (tb);
  tb = NULL;
  exit(0);
}
