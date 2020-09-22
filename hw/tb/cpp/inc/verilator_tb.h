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

#include "verilated.h"
#if VM_TRACE
    #include "verilated_vcd_c.h"
#endif

#include <string>

class VerilatorTb {
 public:
     explicit VerilatorTb(uint32_t port_size, int argc, char** argv);
    ~VerilatorTb();

    // Test input file handlers
    bool ReadTest(uint8_t* buffer);

    // Accessors
    uint32_t get_test_num();

 private:
    // Test tracking data
    uint32_t test_num_;

    // Input port size
    const uint32_t kPortSize_;

    // Verilator configuration driver
    void InitializeVerilator(int argc, char** argv);
};
#endif  // HW_TB_CPP_INC_VERILATOR_TB_H_
