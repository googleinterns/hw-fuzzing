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

#ifndef HW_TB_CPP_INCLUDE_RFUZZ_TB_H_
#define HW_TB_CPP_INCLUDE_RFUZZ_TB_H_

#include "hw/tb/cpp/include/stdin_fuzz_tb.h"

class RFUZZTb : public STDINFuzzTb {
 public:
  RFUZZTb(int argc, char** argv);
  ~RFUZZTb();
  void SimulateDUT();

 private:
  void InitializeDUT();
  bool ResetDUT();
};

#endif  // HW_TB_CPP_INCLUDE_RFUZZ_TB_H_
