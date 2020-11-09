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

#include "hw/tb/cpp/include/ot_ip_fuzz_tb.h"

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

#ifdef OPCODE_TYPE_MAPPED

// This maps each opcode to a range of values rather than to a fixed value
bool OTIPFuzzTb::GetFuzzOpcode(HWFuzzOpcode* opcode) {
  uint8_t opcode_int = 0;
  bool read_valid = ReadBytes(&opcode_int, OPCODE_SIZE_BYTES);
  if (!read_valid) {
    *opcode = HWFuzzOpcode::kInvalid;
  } else if (opcode_int < WAIT_OPCODE_THRESHOLD) {
    *opcode = HWFuzzOpcode::kWait;
  } else if (opcode_int < RW_OPCODE_THRESHOLD) {
    *opcode = HWFuzzOpcode::kRead;
  } else {
    *opcode = HWFuzzOpcode::kWrite;
  }
  return read_valid;
}

#else

// This maps each opcode to a fixed constant value
bool OTIPFuzzTb::GetFuzzOpcode(HWFuzzOpcode* opcode) {
  uint8_t opcode_int = 0;
  bool read_valid = ReadBytes(&opcode_int, OPCODE_SIZE_BYTES);
  if (!read_valid) {
    *opcode = HWFuzzOpcode::kInvalid;
  } else {
    switch (opcode_int) {
      case (uint8_t)HWFuzzOpcode::kWait:
        *opcode = HWFuzzOpcode::kWait;
        break;
      case (uint8_t)HWFuzzOpcode::kRead:
        *opcode = HWFuzzOpcode::kRead;
        break;
      case (uint8_t)HWFuzzOpcode::kWrite:
        *opcode = HWFuzzOpcode::kWrite;
        break;
      default:
        *opcode = HWFuzzOpcode::kInvalid;
        break;
    }
  }
  return read_valid;
}

#endif

#ifdef INSTR_TYPE_FIXED

// This reads a FIXED size HW fuzzing instruction frame from STDIN
bool OTIPFuzzTb::GetFuzzInstruction(HWFuzzInstruction* instr) {
  bool read_valid = false;

  // Get opcode
  read_valid = GetFuzzOpcode(&(instr->opcode));

  // Get address
  if (read_valid) {
    read_valid &= ReadBytes(reinterpret_cast<uint8_t*>(&(instr->address)),
                            ADDRESS_SIZE_BYTES);

    // Get data
    if (read_valid) {
      read_valid &= ReadBytes(reinterpret_cast<uint8_t*>(&(instr->data)),
                              DATA_SIZE_BYTES);
    }
  }
  return read_valid;
}

#else

// This reads a VARIABLE size HW fuzzing instruction frame from STDIN
bool OTIPFuzzTb::GetFuzzInstruction(HWFuzzInstruction* instr) {
  bool read_valid = false;

  // Get opcode
  read_valid = GetFuzzOpcode(&(instr->opcode));

  // Get address and data (if required)
  if (read_valid) {
    switch (instr->opcode) {
      case HWFuzzOpcode::kRead: {
        read_valid &= ReadBytes(reinterpret_cast<uint8_t*>(&(instr->address)),
                                ADDRESS_SIZE_BYTES);
        break;
      }
      case HWFuzzOpcode::kWrite: {
        read_valid &= ReadBytes(reinterpret_cast<uint8_t*>(&(instr->address)),
                                ADDRESS_SIZE_BYTES);
        if (read_valid) {
          read_valid &= ReadBytes(reinterpret_cast<uint8_t*>(&(instr->data)),
                                  DATA_SIZE_BYTES);
        }
        break;
      }
      default:
        // kWait or kInvalid opcodes read nothing additional
        break;
    }
  }
  return read_valid;
}
#endif

void OTIPFuzzTb::SimulateDUT() {
  // Print fuzzing instruction configurations
  std::cout << "---------------------------------" << std::endl;
  std::cout << "Opcode Type:       ";
#ifdef OPCODE_TYPE_MAPPED
  std::cout << "mapped" << std::endl;
#else
  std::cout << "constant" << std::endl;
#endif
  std::cout << "Instruction Type:  ";
#ifdef INSTR_TYPE_FIXED
  std::cout << "fixed" << std::endl;
#else
  std::cout << "variable" << std::endl;
#endif
  std::cout << "Termination Style: ";
#ifdef TERMINATE_ON_INVALID_OPCODE
  std::cout << "invalid opcode" << std::endl;
#else
  std::cout << "eof" << std::endl;
#endif
  std::cout << "---------------------------------" << std::endl;

  // Reset the DUT (check if reset completes before reaching a $finish)
  bool reset_caused_finished =
      ResetDUT(&dut_.clk_i, &dut_.rst_ni, NUM_RESET_CLK_PERIODS);
  std::cout << "---------------------------------" << std::endl;

  // Initialize AFL fork server
#ifdef __AFL_HAVE_MANUAL_CONTROL
  __AFL_INIT();
#endif

  if (!reset_caused_finished) {
    HWFuzzInstruction instr{HWFuzzOpcode::kInvalid, 0, 0};
    bool instr_valid = false;
    uint32_t read_data = 0;  // Data read from TL Get transaction

    // Read tests from file/STDIN and simulate DUT
    std::cout << "Running fuzzer generated tests..." << std::endl;
    instr_valid = GetFuzzInstruction(&instr);
#ifdef TERMINATE_ON_INVALID_OPCODE
    while (instr_valid && (instr.opcode != HWFuzzOpcode::kInvalid) &&
           !Verilated::gotFinish()) {
#else
    while (instr_valid && !Verilated::gotFinish()) {
#endif
      switch (instr.opcode) {
        case HWFuzzOpcode::kWait: {
          std::cout << "(wait)" << std::endl;
          break;
        }

        case HWFuzzOpcode::kRead: {
          // TODO(ttrippel): deal with error/finish (data == 0xFFFFFFFF)
          std::cout << "(read) -- addr: 0x" << std::setw(OT_TL_DW >> 2)
                    << std::setfill('0') << std::hex << instr.address;
          read_data = Get(instr.address);
          std::cout << " --> data: 0x" << std::setw(OT_TL_DW >> 2) << std::hex
                    << read_data << std::endl;
          break;
        }

        case HWFuzzOpcode::kWrite: {
          std::cout << "(write) -- addr: 0x" << std::setw(OT_TL_DW >> 2)
                    << std::setfill('0') << std::hex << instr.address
                    << "; data: 0x" << std::setw(OT_TL_DW >> 2) << std::hex
                    << instr.data << std::endl;
          PutFull(instr.address, instr.data);
          break;
        }

        default: {
          // Handles a kInvalid fuzz opcode
          break;
        }
      }

      // Toggle clock period
      ToggleClock(&dut_.clk_i, 2);

      // Get next fuzzing instruction
      instr_valid = GetFuzzInstruction(&instr);
    }

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
