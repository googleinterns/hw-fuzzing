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

#ifndef HW_TB_CPP_INCLUDE_OT_IP_FUZZ_TB_H_
#define HW_TB_CPP_INCLUDE_OT_IP_FUZZ_TB_H_

#include "hw/tb/cpp/include/tlul_host_tb.h"
#include "hw/tb/cpp/include/verilator_tb.h"

#define OPCODE_SIZE_BYTES 1   // number of opcode bytes to read from STDIN
#define REPEAT_SIZE_BYTES 3   // size of num_repeats value
#define ADDRESS_SIZE_BYTES 4  // size of TL-UL address bus
#define DATA_SIZE_BYTES 4     // size of TL-UL data bus
#define WAIT_OPCODE_THRESHOLD 85
#define RW_OPCODE_THRESHOLD 170
#define NUM_RESET_CLK_PERIODS 1

enum class HWFuzzOpcode {
  kInvalid = 0,
  kWait = 1,
  kRead = 2,
  kWrite = 3,
};

struct HWFuzzInstruction {
  HWFuzzOpcode opcode;
  uint32_t num_repeats;
  uint32_t address;
  uint32_t data;
};

class OTIPFuzzTb : public TLULHostTb {
 public:
  OTIPFuzzTb(int argc, char** argv);
  ~OTIPFuzzTb();
  void SimulateDUT();

 private:
  void InitializeDUT();
  bool ResetDUT(uint32_t num_clk_periods);
  bool GetFuzzOpcode(HWFuzzOpcode* opcode);
  bool GetFuzzInstruction(HWFuzzInstruction* instr);
};

#endif  // HW_TB_CPP_INCLUDE_OT_IP_FUZZ_TB_H_
