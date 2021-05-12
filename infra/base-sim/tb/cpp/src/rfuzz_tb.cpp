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

// TODO(ttrippel): these are specific to the Sodor3Stage design. Need to port
// the dut_gen.py script from the RFUZZ project to autogenerate this.
static constexpr size_t InputSize = 8;
static inline void apply_input(Vtop* top, const uint8_t* input) {
  top->io_input_bytes_0 = input[0];
  top->io_input_bytes_1 = input[1];
  top->io_input_bytes_2 = input[2];
  top->io_input_bytes_3 = input[3];
  top->io_input_bytes_4 = input[4];
  top->io_input_bytes_5 = input[5];
  top->io_input_bytes_6 = input[6];
  top->io_input_bytes_7 = input[7];
}

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

    //// Print test read from file/STDIN
    // std::cout << "Loading inputs for test " << get_test_num();
    // std::cout << " (time = " << std::dec << unsigned(get_main_time())
    //<< ") ...";
    // std::cout << std::endl;
    // std::cout << "  in = " << std::bitset<8>(test_input[0]);
    // std::cout << " (0x" << std::hex << unsigned(test_input[0]) << ")";
    // std::cout << std::endl;
    // std::cout << "  dut.code = " << std::bitset<8>(dut_.code);
    // std::cout << " (0x" << std::hex << unsigned(dut_.code) << ")";
    // std::cout << std::endl;

    // Toggle clock period
    ToggleClock(&dut_.clock, 2);

    // Print vital DUT state
    // std::cout << "Checking if unlocked (time = ";
    // std::cout << std::dec << unsigned(get_main_time()) << ") ..." <<
    // std::endl; std::cout << "  state = 0x" << std::hex <<
    // unsigned(dut_.state)
    //<< std::endl;
    // std::cout << "  unlocked = 0x" << std::hex << unsigned(dut_.unlocked)
    //<< std::endl;
  }

#if VM_TRACE
  // Toggle half a clock period
  ToggleClock(&dut_.clock, 1);
#endif

  // Final model cleanup
  dut_.final();
}
