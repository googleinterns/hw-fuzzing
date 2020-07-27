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

#ifndef DOUBLE_COUNTER_TEST_H_
#define DOUBLE_COUNTER_TEST_H_

#include "verilator_test.h"
#include "Vdouble_counter.h"

// DUT parameters
#define INPUT_PORT_SIZE_BYTES 1
#define NUM_RESET_PERIODS 1

class DoubleCounterTest {
 public:
    explicit DoubleCounterTest(int argc, char** argv);
    ~DoubleCounterTest();

    // DUT drivers
    void ResetDUT();
    void SimulateDUT();

 private:
    // Verification state
    uint32_t num_checks_;

    // Simulation state
    vluint64_t main_time_;  // current simulation time (64-bit unsigned)

    // Verilator SW model of the DUT
    Vdouble_counter dut_;
    VerilatorTest test_;

    // Correct "ground truth" state
    uint8_t count_1_;
    uint8_t count_2_;

#if VM_TRACE
    // VCD tracing
    VerilatedVcdC* tracing_file_pointer_;
    std::string vcd_file_name_;
    void InitializeTracing(std::string fname);
#endif

    // DUT drivers
    void InitializeDUT();
    void ToggleClock(uint32_t num_toggles);
};
#endif