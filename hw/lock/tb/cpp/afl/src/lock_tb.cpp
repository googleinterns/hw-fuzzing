// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "hw/lock/tb/cpp/afl/inc/lock_tb.h"

#include <iostream>

// Constructor
LockTb::LockTb(int argc, char** argv) : VerilatorTb(argc, argv) {
  InitializeDUT();
}

// Destructor
LockTb::~LockTb() {}

// Initialize DUT inputs
void LockTb::InitializeDUT() {
  dut.clk = 0;
  dut.reset_n = 0;
  dut.code = 0;
  dut.eval();
#if VM_TRACE
  // Dump VCD trace for current time
  DumpTrace();
#endif
  main_time++;
}

// Toggle clock for num_toggles half clock periods.
// Model is evaluated AFTER clock state is toggled,
// and regardless of current clock state.
void LockTb::ToggleClock(uint32_t num_toggles) {
  for (uint32_t i = 0; i < num_toggles; i++) {
    // Toggle main clock
    if (dut.clk) {
      dut.clk = 0;
    } else {
      dut.clk = 1;
    }

    // Evaluate model
    dut.eval();

#if VM_TRACE
    // Dump VCD trace for current time
    DumpTrace();
#endif

    // Increment Time
    main_time++;
  }
}

// Reset the DUT
void LockTb::ResetDUT() {
  // Print reset status
  std::cout << "Resetting the DUT (time: " << unsigned(main_time);
  std::cout << ") ..." << std::endl;

  // Place DUT in reset
  dut.reset_n = 0;

  // Toggle clock for NUM_RESET_PERIODS
  ToggleClock((NUM_RESET_PERIODS * 2) + 1);

  // Pull DUT out of reset
  dut.reset_n = 1;

  // Print reset status
  std::cout << "Reset complete! (time = " << unsigned(main_time);
  std::cout << ")" << std::endl;
}

// Simulate the DUT with testbench input file
void LockTb::SimulateDUT() {
  // Create buffer for test data
  uint8_t test_input[INPUT_PORT_SIZE_BYTES] = {0};

  // Read tests and simulate DUT
  while (ReadBytes(test_input, INPUT_PORT_SIZE_BYTES) &&
         !Verilated::gotFinish()) {
    // Load test into DUT
    dut.code = (test_input[0]);

    // Print test read from file
    std::cout << "Loading inputs for test " << test_num;
    std::cout << " (time = " << unsigned(main_time) << ") ...";
    std::cout << std::endl;
    std::cout << "  in = " << std::bitset<8>(test_input[0]);
    std::cout << " (0x" << std::hex << unsigned(test_input[0]) << ")";
    std::cout << std::endl;
    std::cout << "  dut.code = " << std::bitset<8>(dut.code);
    std::cout << " (0x" << std::hex << unsigned(dut.code) << ")";
    std::cout << std::endl;

    // Update correct "ground truth" model state if necessary

    // Toggle clock period
    ToggleClock(2);

    // Print vital DUT state
    std::cout << "Checking if unlocked (time = ";
    std::cout << unsigned(main_time) << ") ..." << std::endl;
    std::cout << "  state = " << unsigned(dut.state) << std::endl;
    std::cout << "  unlocked = " << unsigned(dut.unlocked) << std::endl;

    // Verify vital DUT state
    assert(dut.unlocked == 0 && "SUCCESS: unlocked state has been reached!");
    num_checks++;
  }

#if VM_TRACE
  // Toggle clock period
  ToggleClock(1);
#endif

  // Final model cleanup
  dut.final();
}

// Testbench entry point
int main(int argc, char** argv, char** env) {
  // Instantiate testbench
  LockTb tb(argc, argv);

  // Reset the DUT
  tb.ResetDUT();

  // Simulate the DUT
  tb.SimulateDUT();
}
