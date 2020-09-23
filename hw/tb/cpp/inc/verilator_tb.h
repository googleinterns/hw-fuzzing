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

#ifndef HW_TB_CPP_INC_VERILATOR_TB_H_
#define HW_TB_CPP_INC_VERILATOR_TB_H_

#include "Vtop.h"
#include "verilated.h"
#if VM_TRACE
#include "verilated_vcd_c.h"
#endif

#include <string>

class VerilatorTb {
 public:
  explicit VerilatorTb(int argc, char** argv);  // constructor
  ~VerilatorTb();                               // destructor
  bool ReadBytes(uint8_t* buffer,
                 uint32_t num_bytes);  // reads bytes from STDIN

#if VM_TRACE
  void DumpTrace();  // Dumps VCD trace at current timestamp
#endif

  Vtop dut;              // Verilator SW model of the DUT
  vluint64_t main_time;  // Verilator simulation time
  uint32_t test_num;     // number of fuzz tests run
  uint32_t num_checks;   // number of model checks run

 private:
  void InitializeVerilator(int argc, char** argv);

#if VM_TRACE
  void InitializeTracing(int argc, char** argv);
  VerilatedVcdC* tracing_file_pointer_;  // VCD file pointer
  std::string vcd_file_name_;            // VCD file name
#endif
};

#endif  // HW_TB_CPP_INC_VERILATOR_TB_H_
