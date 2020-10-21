// Copyright 2020 Timothy Trippel
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

#include "hw/lock/tb/cpp/afl_opt/inc/lock_tb.h"

#include <bitset>
#include <iostream>

// Constructor
LockTb::LockTb(int argc, char** argv) : STDINFuzzTb(argc, argv) {
  InitializeDUT();
}

// Destructor
LockTb::~LockTb() {}

// Initialize DUT inputs
void LockTb::InitializeDUT() {
  // Set some sensible values for DUT inputs
  dut_.clk = 0;
  dut_.reset_n = 0;
  dut_.code = 0;

  // Evaluate the Model
  dut_.eval();
#if VM_TRACE
  // Dump VCD trace for current time
  DumpTrace();
#endif

  // Start time at 1 to align rising clock edges with even time values
  set_main_time(1);
}

// Simulate the DUT with testbench input file
void LockTb::SimulateDUT() {
  // Create buffer for test data
  uint8_t test_input[INPUT_PORT_SIZE_BYTES] = {0};

  // Reset the DUT
  ResetDUT(&dut_.clk, &dut_.reset_n, NUM_RESET_CLK_PERIODS);

#ifdef __AFL_HAVE_MANUAL_CONTROL
  __AFL_INIT();
#endif

  // Read tests and simulate DUT
  while (ReadBytes(test_input, INPUT_PORT_SIZE_BYTES) &&
         !Verilated::gotFinish()) {
    // Load test into DUT
    dut_.code = (test_input[0]);

    // Print test read from file/STDIN
    std::cout << "Loading inputs for test " << get_test_num();
    std::cout << " (time = " << std::dec << unsigned(get_main_time())
              << ") ...";
    std::cout << std::endl;
    std::cout << "  in = " << std::bitset<8>(test_input[0]);
    std::cout << " (0x" << std::hex << unsigned(test_input[0]) << ")";
    std::cout << std::endl;
    std::cout << "  dut.code = " << std::bitset<8>(dut_.code);
    std::cout << " (0x" << std::hex << unsigned(dut_.code) << ")";
    std::cout << std::endl;

    // Update correct "ground truth" model state if necessary

    // Toggle clock period
    ToggleClock(&dut_.clk, 2);

    // Print vital DUT state
    std::cout << "Checking if unlocked (time = ";
    std::cout << std::dec << unsigned(get_main_time()) << ") ..." << std::endl;
    std::cout << "  state = 0x" << std::hex << unsigned(dut_.state)
              << std::endl;
    std::cout << "  unlocked = 0x" << std::hex << unsigned(dut_.unlocked)
              << std::endl;

    // Verify vital DUT state
    // assert(dut_.unlocked == 0 && "SUCCESS: unlocked state has been
    // reached!");
  }

#if VM_TRACE
  // Toggle half a clock period
  ToggleClock(&dut_.clk, 1);
#endif

  // Final model cleanup
  dut_.final();
}
