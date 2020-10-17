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

#include <string>

#include "Vtop.h"
#include "verilated.h"
#if VM_TRACE
#include "verilated_vcd_c.h"
#endif

class VerilatorTb {
 public:
  VerilatorTb(int argc, char** argv);
  ~VerilatorTb();
  virtual bool ResetDUT(vluint8_t* clk, vluint8_t* rst_n,
                        uint32_t num_clk_periods);
  vluint64_t get_main_time();

 protected:
  Vtop dut_;  // Verilator model of DUT
#if VM_TRACE
  void DumpTrace();
#endif
  bool ToggleClock(vluint8_t* clk, uint32_t num_toggles);
  void set_main_time(vluint64_t main_time);

 private:
  vluint64_t main_time_;  // Verilator simulation time
#if VM_TRACE
  VerilatedVcdC* tracing_file_pointer_;  // VCD file pointer
  std::string vcd_file_name_;            // VCD file name
  void InitializeTracing(int argc, char** argv);
#endif
  void InitializeVerilator(int argc, char** argv);
};

#endif  // HW_TB_CPP_INC_VERILATOR_TB_H_
