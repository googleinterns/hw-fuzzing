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

#include "lock_test.h"

#include <bitset>
#include <iostream>

// Constructor
LockTest::LockTest(int argc, char** argv)
    : num_checks_(0),
      main_time_(0),
      dut_(),
      test_(INPUT_PORT_SIZE_BYTES, argc, argv)
#if VM_TRACE
      ,
      tracing_file_pointer_(NULL),
      vcd_file_name_("")
#endif
{
#if VM_TRACE
    // Initialize VCD tracing
    InitializeTracing(argv[1]);
#endif

    // Initialize DUT model
    InitializeDUT();
}

// Destructor
LockTest::~LockTest() {
#if VM_TRACE
    // Close VCD trace if opened
    if (tracing_file_pointer_) {
        tracing_file_pointer_->close();
        delete tracing_file_pointer_;
        tracing_file_pointer_ = NULL;
    }
#endif
}

#if VM_TRACE
// Enable Verilator VCD tracing
void LockTest::InitializeTracing(std::string fname) {
    // If verilator was invoked with --trace argument enable VCD tracing
    std::cout << "Tracing enabled." << std::endl;

    // Set VCD file name
    if (fname.find_last_of("\\/") != std::string::npos) {
        // input file name was a full path --> strip off base file name
        uint32_t base_file_name_start = fname.find_last_of("\\/") + 1;
        vcd_file_name_ = fname.substr(base_file_name_start) + ".vcd";
    } else {
        vcd_file_name_ = fname + ".vcd";
    }
    std::cout << "VCD file: " << vcd_file_name_ << std::endl;

    // Turn on Verilator tracing
    Verilated::traceEverOn(true);  // Verilator must compute traced signals
    tracing_file_pointer_ = new VerilatedVcdC();
    dut_.trace(tracing_file_pointer_, 99);  // Trace 99 levels of hierarchy
    tracing_file_pointer_->open(vcd_file_name_.c_str());  // Open the dump file
}
#endif

// Initialize DUT inputs
void LockTest::InitializeDUT() {
    dut_.clk = 0;
    dut_.reset_n = 0;
    dut_.in = 0;
    dut_.eval();
#if VM_TRACE
    // Dump VCD trace for current time
    if (tracing_file_pointer_) {
        tracing_file_pointer_->dump(main_time_);
    }
#endif
    main_time_++;
}

// Toggle clock for num_toggles half clock periods.
// Model is evaluated AFTER clock state is toggled,
// and regardless of current clock state.
void LockTest::ToggleClock(uint32_t num_toggles) {
    for (uint32_t i = 0; i < num_toggles; i++) {
        // Toggle main clock
        if (dut_.clk) {
            dut_.clk = 0;
        } else {
            dut_.clk = 1;
        }

        // Evaluate model
        dut_.eval();

#if VM_TRACE
        // Dump VCD trace for current time
        if (tracing_file_pointer_) {
            tracing_file_pointer_->dump(main_time_);
        }
#endif

        // Increment Time
        main_time_++;
    }
}

// Reset the DUT
void LockTest::ResetDUT() {
    // Print reset status
    std::cout << "Resetting the DUT (time: " << unsigned(main_time_);
    std::cout << ") ..." << std::endl;

    // Place DUT in reset
    dut_.reset_n = 0;

    // Toggle clock for NUM_RESET_PERIODS
    ToggleClock((NUM_RESET_PERIODS * 2) + 1);

    // Pull DUT out of reset
    dut_.reset_n = 1;

    // Print reset status
    std::cout << "Reset complete! (time = " << unsigned(main_time_);
    std::cout << ")" << std::endl;
}

// Simulate the DUT with testbench input file
void LockTest::SimulateDUT() {
    // Create buffer for test data
    uint8_t test_input[INPUT_PORT_SIZE_BYTES] = {0};

    // Read tests and simulate DUT
    while (test_.ReadTest(test_input) && !Verilated::gotFinish()) {
        // Load test into DUT
        dut_.in = (test_input[0]);

        // Print test read from file
        std::cout << "Loading inputs for test " << test_.get_test_num();
        std::cout << " (time = " << unsigned(main_time_) << ") ...";
        std::cout << std::endl;
        std::cout << "  in = " << std::bitset<8>(test_input[0]);
        std::cout << " (0x" << std::hex << unsigned(test_input[0]) << ")";
        std::cout << std::endl;
        std::cout << "  dut.in = " << std::bitset<8>(dut_.in);
        std::cout << " (0x" << std::hex << unsigned(dut_.in) << ")";
        std::cout << std::endl;

        // Update correct "ground truth" state
        // N/A

        // Toggle clock period
        ToggleClock(2);

        // Print vital DUT state
        std::cout << "Checking if unlocked (time = ";
        std::cout << unsigned(main_time_) << ") ..." << std::endl;
        std::cout << "  state = " << unsigned(dut_.state) << std::endl;
        std::cout << "  unlocked = " << unsigned(dut_.unlocked) << std::endl;

        // Verify vital DUT state
        assert(dut_.unlocked == 0 &&
            "SUCCESS: unlocked state has been reached!");
        num_checks_++;
    }

#if VM_TRACE
    // Toggle clock period
    ToggleClock(1);
#endif

    // Final model cleanup
    dut_.final();
}

// Testbench entry point
int main(int argc, char** argv, char** env) {
    // Check command line args
    if (argc == 2) {
        std::cout << "Input file: " << argv[1] << std::endl;
    } else {
        std::cerr << "Usage: " << argv[0];
        std::cerr << " <input file name>" << std::endl;
        exit(1);
    }

    // Instantiate testbench
    LockTest tb(argc, argv);

    // Reset the DUT
    tb.ResetDUT();

    // Simulate the DUT
    tb.SimulateDUT();
}
