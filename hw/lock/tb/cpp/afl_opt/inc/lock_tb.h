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

#ifndef HW_LOCK_TB_CPP_AFL_OPT_INC_LOCK_TB_H_
#define HW_LOCK_TB_CPP_AFL_OPT_INC_LOCK_TB_H_

#include "hw/tb/cpp/inc/stdin_fuzz_tb.h"

// DUT parameters
#define INPUT_PORT_SIZE_BYTES 1
#define NUM_RESET_CLK_PERIODS 1

class LockTb : public STDINFuzzTb {
 public:
  LockTb(int argc, char** argv);
  ~LockTb();
  void SimulateDUT();

 private:
  void InitializeDUT();
};

#endif  // HW_LOCK_TB_CPP_AFL_OPT_INC_LOCK_TB_H_
