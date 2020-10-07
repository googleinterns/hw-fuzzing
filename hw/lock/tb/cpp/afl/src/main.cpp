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

#include "hw/lock/tb/cpp/afl/inc/lock_tb.h"

// Testbench needs to be global for sc_time_stamp()
LockTb* tb = NULL;

// needs to be defined so Verilog can call $time
double sc_time_stamp() { return tb->get_main_time(); }

int main(int argc, char** argv, char** env) {
  // Instantiate testbench
  tb = new LockTb(argc, argv);

  // Simulate the DUT
  tb->SimulateDUT();

  // Teardown
  delete (tb);
  tb = NULL;
  exit(0);
}
