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
    : main_time(0),
      dut(),
      test_num(0),
      num_checks(0)
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

// Read num_bytes from input file stream into buffer
bool VerilatorTb::ReadBytes(uint8_t* buffer, uint32_t num_bytes) {
  if (!std::cin.eof()) {
    // Read file as a byte stream
    std::cin.read((char*)buffer, num_bytes);
    if (std::cin.gcount() < num_bytes) {
      return false;
    }
    // Increment test number
    test_num++;
    return true;
  }
  return false;
}

#if VM_TRACE
void VerilatorTb::DumpTrace() {
  if (tracing_file_pointer_) {
    tracing_file_pointer_->dump(main_time);
  } else {
    std::cout << "WARNING: cannot dump VCD trace at time: " << main_time
              << std::endl;
  }
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

#if VM_TRACE
// Enable Verilator VCD tracing
void VerilatorTb::InitializeTracing(int argc, char** argv) {
  // If verilator was invoked with --trace argument enable VCD tracing
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
  dut.trace(tracing_file_pointer_, 99);  // Trace 99 levels of hierarchy
  tracing_file_pointer_->open(vcd_file_name_.c_str());  // Open the dump file
}
#endif
