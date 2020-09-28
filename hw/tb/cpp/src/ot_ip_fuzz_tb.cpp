// TODO(ttrippel): add license

#include "hw/tb/cpp/inc/ot_ip_fuzz_tb.h"

#include <stdlib.h>

#include <iomanip>
#include <iostream>

// Constructor
OTIPFuzzTb::OTIPFuzzTb(int argc, char** argv) : TLULHostTb(argc, argv) {
  address_size_bytes_ = atoi(getenv(ADDRESS_SIZE_BYTES_ENV_VAR));
  data_size_bytes_ = atoi(getenv(DATA_SIZE_BYTES_ENV_VAR));
  InitializeDUT();
}

// Destructor
OTIPFuzzTb::~OTIPFuzzTb() {}

// Initialize DUT inputs
void OTIPFuzzTb::InitializeDUT() {
  // Set some sensible values for DUT inputs
  dut_.clk_i = 0;
  dut_.rst_ni = 0;

  // Evaluate the Model
  dut_.eval();
#if VM_TRACE
  // Dump VCD trace for current time
  DumpTrace();
#endif

  // Start time at 1 to align rising clock edges with even time values
  set_main_time(1);
}

HWFuzzOpcode OTIPFuzzTb::GetFuzzerOpcode() {
  uint8_t opcode = 0;
  bool read_valid = ReadBytes(&opcode, OPCODE_SIZE_BYTES);
  if (!read_valid) {
    return HWFuzzOpcode::kInvalid;
  } else if (opcode < WAIT_OPCODE_THRESHOLD) {
    return HWFuzzOpcode::kWait;
  } else if (opcode < RW_OPCODE_THRESHOLD) {
    return HWFuzzOpcode::kRead;
  } else {
    return HWFuzzOpcode::kWrite;
  }
}

TLULAddress OTIPFuzzTb::GetTLULAddress() {
  TLULAddress address{false, 0};
  address.valid = ReadBytes(reinterpret_cast<uint8_t*>(&address.address),
                            address_size_bytes_);
  return address;
}

TLULData OTIPFuzzTb::GetTLULData() {
  TLULData data{false, 0};
  data.valid =
      ReadBytes(reinterpret_cast<uint8_t*>(&data.data), data_size_bytes_);
  return data;
}

void OTIPFuzzTb::SimulateDUT() {
  // Reset the DUT
  ResetDUT(&dut_.clk_i, &dut_.rst_ni, NUM_RESET_CLK_PERIODS);

  HWFuzzOpcode fuzzer_opcode = HWFuzzOpcode::kInvalid;
  TLULAddress rw_address{false, 0};
  TLULAddress w_data{false, 0};
  uint32_t r_data = 0;

  // Read tests from file/STDIN and simulate DUT
  std::cout << "Running fuzzer generated tests..." << std::endl;
  do {
    fuzzer_opcode = GetFuzzerOpcode();

    switch (fuzzer_opcode) {
      case HWFuzzOpcode::kWait: {
        std::cout << "(wait)" << std::endl;
        break;
      }

      case HWFuzzOpcode::kRead: {
        rw_address = GetTLULAddress();
        if (rw_address.valid) {
          std::cout << "(read) -- addr: 0x" << std::setw(OT_TL_DW >> 2)
                    << std::hex << rw_address.address << "; data: 0x"
                    << std::setw(OT_TL_DW >> 2) << std::hex << r_data
                    << std::endl;
          r_data = Get(rw_address.address);
        } else {
          std::cout << "No more fuzzer input... ending test." << std::endl;
        }
        break;
      }

      case HWFuzzOpcode::kWrite: {
        break;
      }

      default: {
        std::cout << "ERROR: Invalid fuzzer opcode: " << (uint32_t)fuzzer_opcode
                  << std::endl;
        break;
      }
    }

    // Update correct "ground truth" model state if necessary

    // Toggle clock period
    ToggleClock(&dut_.clk_i, 2);

    // Print vital DUT state
    // Verify vital DUT state
  } while (fuzzer_opcode != HWFuzzOpcode::kInvalid && !Verilated::gotFinish());

  std::cout << "Fuzz tests completed!" << std::endl;
#if VM_TRACE
  // Toggle half a clock period
  ToggleClock(&dut_.clk_i, 1);
#endif

  // Final model cleanup
  dut_.final();
}
