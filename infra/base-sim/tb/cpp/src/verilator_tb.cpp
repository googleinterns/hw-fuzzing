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

#include "hw/tb/cpp/inc/verilator_tb.h"

#include <iostream>

// Constructor: initialize Verilator, and open a VCD trace and the testbench
// input file
VerilatorTb::VerilatorTb(int argc, char** argv)
    : dut_(),
      main_time_(0)
#if VM_TRACE
      ,
      tracing_file_pointer_(NULL),
      vcd_file_name_("")
#endif
{
  InitializeVerilator(argc, argv);
#if VM_TRACE
  InitializeTracing(argc, argv);
#endif
}

// Destructor: close testbench input and VCD files, report coverage, and destroy
// model
VerilatorTb::~VerilatorTb() {
#if VM_TRACE
  // Close VCD trace if opened
  if (tracing_file_pointer_) {
    tracing_file_pointer_->close();
    delete tracing_file_pointer_;
    tracing_file_pointer_ = NULL;
  }
#endif
#if VM_COVERAGE
  //  Save coverage analysis (since test passed)
  Verilated::mkdir("logs");
  VerilatedCov::write("logs/coverage.dat");
#endif
}

// Reset the DUT
bool VerilatorTb::ResetDUT(vluint8_t* clk, vluint8_t* rst_n,
                           uint32_t num_clk_periods) {
  // Print reset status
  std::cout << "Resetting the DUT (time: " << std::dec << unsigned(main_time_);
  std::cout << ") ..." << std::endl;

  // Place DUT in reset
  *rst_n = 0;

  // Toggle clock for NUM_RESET_PERIODS
  // Check if reached end of simulation
  if (ToggleClock(clk, (num_clk_periods * 2) + 1)) {
    return true;
  }

  // Pull DUT out of reset
  *rst_n = 1;

  // Print reset status
  std::cout << "Reset complete! (time = " << std::dec << unsigned(main_time_);
  std::cout << ")" << std::endl;

  // Indicate we have NOT reached a Verilog $finish statement
  return false;
}

#if VM_TRACE
// Dump VCD trace to VCD file
void VerilatorTb::DumpTrace() {
  if (tracing_file_pointer_) {
    tracing_file_pointer_->dump(main_time_);
  } else {
    std::cout << "WARNING: cannot dump VCD trace at time: " << std::dec
              << main_time_ << std::endl;
  }
}
#endif

// Toggle clock for num_toggles half clock periods.
// Model is evaluated AFTER clock state is toggled,
// and regardless of current clock state.
bool VerilatorTb::ToggleClock(vluint8_t* clk, uint32_t num_toggles) {
  for (uint32_t i = 0; i < num_toggles; i++) {
    // Toggle main clock
    if (*clk) {
      *clk = 0;
    } else {
      *clk = 1;
    }

    // Evaluate model
    dut_.eval();

#if VM_TRACE
    // Dump VCD trace for current time
    DumpTrace();
#endif

    // Increment Time
    main_time_++;

    // Check if reached end of simulation
    if (Verilated::gotFinish()) {
      return true;
    }
  }

  return false;
}

// main_time_ accessor
vluint64_t VerilatorTb::get_main_time() { return main_time_; }

// main_time_ setter
void VerilatorTb::set_main_time(vluint64_t main_time) {
  main_time_ = main_time;
}

#if VM_TRACE
// Enable Verilator VCD tracing
void VerilatorTb::InitializeTracing(int argc, char** argv) {
  // If verilator was invoked with --trace argument enable VCD tracing
  std::cout << "---------------------------------" << std::endl;
  std::cout << "Tracing enabled." << std::endl;

  // Check if VCD filename provided
  if (argc == 2) {
    std::string fname = argv[1];
    // Set VCD file name
    if (fname.find_last_of("\\/") != std::string::npos) {
      // input file name was a full path --> strip off base file name
      uint32_t base_file_name_start = fname.find_last_of("\\/") + 1;
      vcd_file_name_ = fname.substr(base_file_name_start) + ".vcd";
    } else {
      vcd_file_name_ = fname + ".vcd";
    }
  } else {
    vcd_file_name_ = "trace.vcd";
  }
  std::cout << "VCD file: " << vcd_file_name_ << std::endl;

  // Turn on Verilator tracing
  Verilated::traceEverOn(true);  // Verilator must compute traced signals
  tracing_file_pointer_ = new VerilatedVcdC();
  dut_.trace(tracing_file_pointer_, 99);  // Trace 99 levels of hierarchy
  tracing_file_pointer_->open(vcd_file_name_.c_str());  // Open the dump file
}
#endif

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
