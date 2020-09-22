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

#include "tb/cpp/inc/verilator_tb.h"

#include <iostream>

// Constructor: initialize Verilator, and open a VCD trace and
// the testbench input file
VerilatorTb::VerilatorTb(uint32_t port_size, int argc, char** argv)
    : test_num_(0),
      kPortSize_(port_size) {
    InitializeVerilator(argc, argv);
}

// Destructor: close testbench input and VCD files, report coverage,
// and destroy model
VerilatorTb::~VerilatorTb() {
    //  Coverage analysis (since test passed)
#if VM_COVERAGE
    Verilated::mkdir("logs");
    VerilatedCov::write("logs/coverage.dat");
#endif
}

// test_num_ accessor
uint32_t VerilatorTb::get_test_num() {
    return test_num_;
}

// Initialize Verilator settings
void VerilatorTb::InitializeVerilator(int argc, char** argv) {
    // Set debug level, 0 is off, 9 is highest presently used
    // May be overridden by commandArgs
    Verilated::debug(0);

    // Randomization reset policy
    // May be overridden by commandArgs
    Verilated::randReset(2);

    // Pass arguments so Verilated code can see them, e.g. $value$plusargs
    // This needs to be called before you create any model
    Verilated::commandArgs(argc, argv);
}

// Read num_bytes from input file stream into buffer
bool VerilatorTb::ReadTest(uint8_t* buffer) {
    if (!std::cin.eof()) {
        // Read file as a byte stream
        std::cin.read((char*) buffer, kPortSize_);
        if (std::cin.gcount() < kPortSize_) {
            return false;
        }
        // Increment test number
        test_num_++;
        return true;
    }
    return false;
}
