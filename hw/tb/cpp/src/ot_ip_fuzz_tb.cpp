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

#include "hw/tb/cpp/inc/ot_ip_fuzz_tb.h"

#include <iomanip>
#include <iostream>

// Constructor
OTIPFuzzTb::OTIPFuzzTb(int argc, char** argv) : TLULHostTb(argc, argv) {
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
    return HWFuzzOpcode::kWrite;
  } else {
    return HWFuzzOpcode::kRead;
  }
}

TLULAddress OTIPFuzzTb::GetTLULAddress() {
  TLULAddress address{false, 0};
  address.valid = ReadBytes(reinterpret_cast<uint8_t*>(&address.address),
                            ADDRESS_SIZE_BYTES);
  return address;
}

TLULData OTIPFuzzTb::GetTLULData() {
  TLULData data{false, 0};
  data.valid =
      ReadBytes(reinterpret_cast<uint8_t*>(&data.data), DATA_SIZE_BYTES);
  return data;
}

void OTIPFuzzTb::SimulateDUT() {
  // Reset the DUT (check if reset completes before reaching a $finish)
  if (!ResetDUT(&dut_.clk_i, &dut_.rst_ni, NUM_RESET_CLK_PERIODS)) {
    HWFuzzOpcode fuzzer_opcode = HWFuzzOpcode::kInvalid;
    TLULAddress rw_address{false, 0};
    TLULData w_data{false, 0};
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
            r_data = Get(rw_address.address);
            // TODO(ttrippel): deal with error/finish (data == 0xFFFFFFFF)
            std::cout << "(read) -- addr: 0x" << std::setw(OT_TL_DW >> 2)
                      << std::setfill('0') << std::hex << rw_address.address
                      << " --> data: 0x" << std::setw(OT_TL_DW >> 2) << std::hex
                      << r_data << std::endl;
          }
          break;
        }

        case HWFuzzOpcode::kWrite: {
          rw_address = GetTLULAddress();
          w_data = GetTLULData();
          if (rw_address.valid && w_data.valid) {
            PutFull(rw_address.address, w_data.data);
            std::cout << "(write) -- addr: 0x" << std::setw(OT_TL_DW >> 2)
                      << std::setfill('0') << std::hex << rw_address.address
                      << "; data: 0x" << std::setw(OT_TL_DW >> 2) << std::hex
                      << w_data.data << std::endl;
          }
          break;
        }

        default: {
          break;
        }
      }

      // Update projected "ground truth" model state

      // Toggle clock period
      ToggleClock(&dut_.clk_i, 2);

      // Verify current state matches projected state

    } while (fuzzer_opcode != HWFuzzOpcode::kInvalid &&
             !Verilated::gotFinish());

    std::cout << "Fuzz tests completed!" << std::endl;
  } else {
    std::cout << "WARNING: reached $finish before end of reset." << std::endl;
  }

#if VM_TRACE
  // Toggle half a clock period
  ToggleClock(&dut_.clk_i, 1);
#endif

  // Final model cleanup
  std::cout << "Simulation complete!" << std::endl;
  dut_.final();
}
