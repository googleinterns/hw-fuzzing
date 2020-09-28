// TODO(ttrippel): add license

#include "hw//tb/cpp/inc/ot_ip_fuzz_tb.h"

int main(int argc, char** argv, char** env) {
  // Instantiate testbench
  OTIPFuzzTb tb(argc, argv);

  // Simulate the DUT
  tb.SimulateDUT();
}
