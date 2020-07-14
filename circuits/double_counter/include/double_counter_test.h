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

#include <fstream>
#include <string>

// Verilator header
#include "verilated.h"

// Include model header, generated from Verilating DUT
#include "Vdouble_counter.h"

// If "verilator --trace" is used, include the tracing class
#if VM_TRACE
    #include "verilated_vcd_c.h"
#endif

// DUT parameters
#define INPUT_PORT_SIZE_IN_BYTES 1
#define NUM_RESET_PERIODS 2

class DoubleCounterTest {
 public:
    DoubleCounterTest(std::string fname);
    ~DoubleCounterTest();
    void ConfigureVerilator(int argc, char** argv);
    void InitializeDUT();
#if VM_TRACE
    void ConfigureTracing();
#endif
    void ResetDUT();
    void SimulateDUT();
    void CleanupSimulation();

 private:
    // Test tracking data
    uint32_t test_num_;
    uint32_t num_bytes_read_from_input_file_;
    uint32_t num_checks_done_;

    // DUT input
    std::string input_file_name_;
    std::ifstream* input_file_stream_;
    uint8_t select_;

    // Correct "ground truth" state
    uint8_t count_1_;
    uint8_t count_2_;

    // Model
    Vdouble_counter* dut_;

    // Simulation state
    vluint64_t main_time_; // current simulation time (64-bit unsigned)
#if VM_TRACE
    VerilatedVcdC* tracing_file_pointer_;
    std::string vcd_file_name_;
#endif

    // Input file handlers
    void OpenSimulationFile();
    uint32_t ReadSimulationInput(uint8_t* buffer, uint32_t num_bytes);
    void CloseSimulationFile();
};
