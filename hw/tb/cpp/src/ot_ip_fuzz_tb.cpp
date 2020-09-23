// TODO(ttrippel): add license

#include "hw/tb/cpp/inc/ot_ip_fuzz_tb.h"

#include <iostream>

// Constructor
OTIPFuzzTb::OTIPFuzzTb(int argc, char** argv)
    : VerilatorTb(INPUT_PORT_SIZE_BYTES, argc, argv) {
  InitializeDUT();
}

// Destructor
OTIPFuzzTb::~OTIPFuzzTb() {}

// Initialize DUT inputs
void OTIPFuzzTb::InitializeDUT() {
  dut.clk_i = 0;
  dut.rst_ni = 0;
  dut.tl_i = 0;
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
void OTIPFuzzTb::ToggleClock(uint32_t num_toggles) {
  for (uint32_t i = 0; i < num_toggles; i++) {
    // Toggle main clock
    if (dut.clk_i) {
      dut.clk_i = 0;
    } else {
      dut.clk_i = 1;
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

uint8_t OTIPFuzzTb::GetFuzzerOpcode() {
  uint8_t opcode = 0;
  ReadBytes(&opcode, OPCODE_SIZE_BYTES);
  return opcode;
}

uint32_t OTIPFuzzTb::GetTLULAddress() {
  uint32_t address = 0;
  ReadBytes(&address, kAddressSizeBytes);
  return address;
}

uint32_t OTIPFuzzTb::GetTLULData() {
  uint32_t data = 0;
  ReadBytes(&data, kDataSizeBytes);
  return data;
}

// Reset the DUT
void OTIPFuzzTb::ResetDUT() {
  // Print reset status
  std::cout << "Resetting the DUT (time: " << unsigned(main_time);
  std::cout << ") ..." << std::endl;

  // Place DUT in reset
  dut.rst_ni = 0;

  // Toggle clock for NUM_RESET_PERIODS
  ToggleClock(NUM_RESET_PERIODS * 2);

  // Pull DUT out of reset
  dut.reset_n = 1;

  // Print reset status
  std::cout << "Reset complete! (time = " << unsigned(main_time);
  std::cout << ")" << std::endl;
}

void OTIPFuzzTb::SimulateDUT() {}
