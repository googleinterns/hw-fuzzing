// TODO(ttrippel): add license

#include "hw/lock/tb/cpp/afl/inc/lock_tb.h"

int main(int argc, char** argv, char** env) {
  // Instantiate testbench
  LockTb tb(argc, argv);

  // Simulate the DUT
  tb.SimulateDUT();
}
