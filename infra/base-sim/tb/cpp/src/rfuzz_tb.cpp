// Copyright 2021 Timothy Trippel
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

#include "hw/tb/cpp/include/rfuzz_tb.h"

#include <bitset>
#include <iostream>

#include "hw/tb/cpp/include/rfuzz_tb_interface.h"

const uint8_t ResetInput[InputSize] = {0};

// Constructor
RFUZZTb::RFUZZTb(int argc, char** argv) : STDINFuzzTb(argc, argv) {
  InitializeDUT();
}

// Destructor
RFUZZTb::~RFUZZTb() {}

// Initialize DUT inputs
void RFUZZTb::InitializeDUT() {
  // Set some sensible values for DUT inputs
  apply_input(&dut_, ResetInput);

  // Evaluate the Model
  dut_.eval();
#if VM_TRACE
  // Dump VCD trace for current time
  DumpTrace();
#endif

  // Start time at 1 to align rising clock edges with even time values
  set_main_time(1);
}

bool RFUZZTb::ResetDUT() {
  // Print reset status
  std::cout << "Resetting the DUT (time: " << std::dec << unsigned(main_time_);
  std::cout << ") ..." << std::endl;

  // Apply reset input to DUT
  apply_input(&dut_, ResetInput);

  // Perform meta reset for 1 clock cycle
  dut_.io_meta_reset = 1;
  if (ToggleClock(&dut_.clock, 2)) {
    return true;
  }
  dut_.io_meta_reset = 0;

  // Perform circuit reset for 1 clock cycle
  dut_.reset = 1;
  if (ToggleClock(&dut_.clock, 2)) {
    return true;
  }
  dut_.reset = 0;

  // Print reset status
  std::cout << "Reset complete! (time = " << std::dec << unsigned(main_time_);
  std::cout << ")" << std::endl;

  // Indicate we have NOT reached a Verilog $finish statement
  return false;
}

// Simulate the DUT with testbench input file
void RFUZZTb::SimulateDUT() {
  // Create buffer for test data
  uint8_t test_input[InputSize] = {0};

  // Reset the DUT
  ResetDUT();

  // Read tests and simulate DUT
  while (ReadBytes(test_input, InputSize) && !Verilated::gotFinish()) {
    // Load test into DUT
    apply_input(&dut_, test_input);

    // Toggle clock period
    ToggleClock(&dut_.clock, 2);
  }

#if VM_TRACE
  // Toggle half a clock period
  ToggleClock(&dut_.clock, 1);
#endif

  // Final model cleanup
  dut_.final();
}
