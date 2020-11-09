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

#ifndef HW_TB_CPP_INCLUDE_STDIN_FUZZ_TB_H_
#define HW_TB_CPP_INCLUDE_STDIN_FUZZ_TB_H_

#include "hw/tb/cpp/include/verilator_tb.h"

class STDINFuzzTb : public VerilatorTb {
 public:
  STDINFuzzTb(int argc, char** argv);
  ~STDINFuzzTb();
  bool ReadBytes(uint8_t* buffer, uint32_t num_bytes);
  uint32_t get_test_num();

 private:
  uint32_t test_num_;  // number of fuzz tests run read from STDIN
};

#endif  // HW_TB_CPP_INCLUDE_STDIN_FUZZ_TB_H_
