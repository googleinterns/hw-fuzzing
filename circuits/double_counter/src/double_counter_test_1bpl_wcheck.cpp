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

#include "double_counter_test.h"

#include <bitset>
#include <iostream>

// Constructor
DoubleCounterTest::DoubleCounterTest(std::string fname)
    : test_num_(0),
      num_bytes_read_from_input_file_(1),
      num_checks_done_(0),
      input_file_name_(fname),
      input_file_stream_(NULL),
      select_(0),
      count_1_(0),
      count_2_(0),
      dut_(NULL),
      main_time_(0)
#if VM_TRACE
      , tracing_file_pointer_(NULL),
      vcd_file_name_("")
#endif
    { OpenSimulationFile(); }

// Destructor
DoubleCounterTest::~DoubleCounterTest() {}

// Open input file stream for reading
void DoubleCounterTest::OpenSimulationFile() {
    input_file_stream_ = new std::ifstream();
    input_file_stream_->open(input_file_name_, std::ifstream::binary);
    if (!input_file_stream_->is_open()) {
        std::cerr << "ERROR: cannot open testbench input file: ";
        std::cerr << input_file_name_ << std::endl;
        exit(1);
    }
}

// Read num_bytes from input file stream into buffer
uint32_t DoubleCounterTest::ReadSimulationInput(
    uint8_t* buffer,
    uint32_t num_bytes) {
    if (!input_file_stream_->eof()) {
        // Assume input is formatted as one input per line;
        input_file_stream_->read((char*) buffer, num_bytes);
        uint32_t num_bytes_read = input_file_stream_->gcount();
        if (num_bytes_read == num_bytes && input_file_stream_) {
            // Read and throw away new line character
            char throw_away = 0;
            input_file_stream_->read(&throw_away, 1);
        }
        return num_bytes_read;
    }
    return 0;
}

// Close input file stream (if it's open)
void DoubleCounterTest::CloseSimulationFile() {
    if (input_file_stream_->is_open()) {
        input_file_stream_->close();
        delete input_file_stream_;
        input_file_stream_ = NULL;
    }
}

// Configure Verilator settings
void DoubleCounterTest::ConfigureVerilator(int argc, char** argv) {
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

// Instantiate DUT model and initialize inputs
void DoubleCounterTest::InitializeDUT() {
    // Instantiate the Verilated model
    dut_ = new Vdouble_counter();

    // Initialize inputs
    dut_->clk = 0;
    dut_->n_reset = 0;
    dut_->select = 0;
}

#if VM_TRACE
// Configure Verilator for VCD tracing
void DoubleCounterTest::ConfigureTracing() {
    // If verilator was invoked with --trace argument enable VCD tracing
    std::cout << "Tracing enabled." << std::endl;

    // Set VCD file name
    if (input_file_name_.find_last_of("\\/") != std::string::npos) {
        // input file name was a full path --> strip off base file name
        uint32_t base_file_name_start =
            input_file_name_.find_last_of("\\/") + 1;
        std::string base_file_name =
            input_file_name_.substr(base_file_name_start);
        vcd_file_name_ = base_file_name + ".vcd";
    } else {
        vcd_file_name_ = input_file_name_ + ".vcd";
    }
    std::cout << "VCD file: " << vcd_file_name_ << std::endl;

    // Turn on Verilator tracing
    Verilated::traceEverOn(true);  // Verilator must compute traced signals
    tracing_file_pointer_ = new VerilatedVcdC();
    dut_->trace(tracing_file_pointer_, 99);  // Trace 99 levels of hierarchy
    tracing_file_pointer_->open(vcd_file_name_.c_str());  // Open the dump file
}
#endif

// Reset the DUT
void DoubleCounterTest::ResetDUT() {
    for (uint8_t i = 0; i < (NUM_RESET_PERIODS * 2); i++) {
        // Evaluate model
        std::cout << "Resetting the DUT " << " (time = ";
        std::cout << unsigned(main_time_) << ") ..." << std::endl;
        dut_->eval();

#if VM_TRACE
        // Dump trace data for this cycle
        if (tracing_file_pointer_) {
            tracing_file_pointer_->dump(main_time_);
        }
#endif

        // Toggle main clock
        if ((main_time_ % 2) == 0) {
            // Toggle clock
            dut_->clk = 1;
        } else {
            // Toggle clock
            dut_->clk = 0;
        }

        // Increment Time
        main_time_++;
    }

    // Pull DUT out of reset
    dut_->n_reset = 1;
}

// Simulate the DUT with testbench input file
void DoubleCounterTest::SimulateDUT() {
    while (!Verilated::gotFinish() && num_bytes_read_from_input_file_) {
        // Evaluate model
        dut_->eval();

#if VM_TRACE
        // Dump trace data for this cycle
        if (tracing_file_pointer_) {
            tracing_file_pointer_->dump(main_time_);
        }
#endif

        // Toggle main clock
        if ((main_time_ % 2) == 0) {
            // Verify Counter Results
            std::cout << "Checking results for test " << num_checks_done_;
            std::cout << " (time = " << unsigned(main_time_) << ") ...";
            std::cout << std::endl;
            std::cout << "  count_1 (DUT / Correct) = ";
            std::cout << unsigned(dut_->count_1) << "/" << unsigned(count_1_);
            std::cout << std::endl;
            std::cout << "  count_2 (DUT / Correct) = ";
            std::cout << unsigned(dut_->count_2) << "/" << unsigned(count_2_);
            std::cout << std::endl;
            assert(count_1_ == dut_->count_1 && \
                "ERROR: Incorrect value for count_1.");
            assert(count_2_ == dut_->count_2 && \
                "ERROR: Incorrect value for count_2.");
            num_checks_done_++;

            // Toggle clock
            dut_->clk = 1;

            // perform increment
            if (select_ & 0x1) {
                count_1_++;
            } else {
                count_2_++;
            }
        } else {
            // Toggle clock
            dut_->clk = 0;

            // Load next input
            num_bytes_read_from_input_file_ = ReadSimulationInput(&select_, 1);

            if (num_bytes_read_from_input_file_) {
                // Increment test number
                test_num_++;

                // load next select into DUT
                std::cout << "Loading inputs for test " << test_num_;
                std::cout << " (time = " << unsigned(main_time_) << ") ...";
                std::cout << std::endl;
                std::cout << "  select = ";
                std::cout << std::bitset<INPUT_PORT_SIZE_IN_BYTES * 8>(select_);
                std::cout << " (0x" << std::hex << unsigned(select_) << ")";
                std::cout << std::endl;
                dut_->select = (select_ & 0x1);
            }
        }

        // Increment time
        main_time_++;
    }
}

void DoubleCounterTest::CleanupSimulation() {
    // Close simulation input file stream
    CloseSimulationFile();

    // Final model cleanup
    dut_->final();

    // Close trace if opened
#if VM_TRACE
    if (tracing_file_pointer_) {
        tracing_file_pointer_->close();
        tracing_file_pointer_ = NULL;
    }
#endif

    //  Coverage analysis (since test passed)
#if VM_COVERAGE
    Verilated::mkdir("logs");
    VerilatedCov::write("logs/coverage.dat");
#endif

    // Destroy model
    delete dut_;
    dut_ = NULL;
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

    // Check the format of the input file & terminate simulation if not correct.
    // This trains AFL to throw away mutations that are not in the correct
    // size format.
    std::ifstream fin(argv[1]);
    std::string line = "";
    while (getline(fin, line)) {
        if (line.length() != 1) {
            exit(0);
        }
    }
    fin.close();

    // Instantiate testbench
    DoubleCounterTest tb(argv[1]);

    // Configure Verilator
    tb.ConfigureVerilator(argc, argv);

    // Initialize the DUT
    tb.InitializeDUT();

#if VM_TRACE
    // Configure Verilator VCD tracing
    tb.ConfigureTracing();
#endif

    // Reset the DUT
    tb.ResetDUT();

    // Simulate the DUT
    tb.SimulateDUT();

    // Cleanup
    tb.CleanupSimulation();

    // Done
    exit(0);
}
