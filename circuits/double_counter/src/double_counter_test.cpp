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

// Include common routines
#include <verilated.h>

// Include model header, generated from Verilating "aes_128.v"
#include "Vdouble_counter.h"

// If "verilator --trace" is used, include the tracing class
#if VM_TRACE
    #include <verilated_vcd_c.h>
#endif

// Standard includes
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
using std::cerr;
using std::cout;
using std::endl;
using std::fstream;
using std::string;

// Testbench Parameters
#define COUNT_SIZE 1
#define NUM_RESET_CYCLES 5

// Current simulation time (64-bit unsigned)
vluint64_t main_time = 0;

// Called by $time in Verilog
double sc_time_stamp() {
    return main_time;  // Note does conversion to real, to match SystemC
}

// Entry point
int main(int argc, char** argv, char** env) {
    // Test Bench Inputs
    fstream in_file;
    uint32_t test_num = 0;
    uint32_t check_num = 0;
    string in_file_name = "";
    string input_select = "";
    uint8_t select = 0;
    uint8_t count_1 = 0;
    uint8_t count_2 = 0;

    // Set debug level, 0 is off, 9 is highest presently used
    // May be overridden by commandArgs
    Verilated::debug(0);

    // Randomization reset policy
    // May be overridden by commandArgs
    Verilated::randReset(2);

    // Pass arguments so Verilated code can see them, e.g. $value$plusargs
    // This needs to be called before you create any model
    Verilated::commandArgs(argc, argv);

    // Construct the Verilated model, from Vdouble_counter.h
    // generated from Verilating "double_counter.v"
    Vdouble_counter* top = new Vdouble_counter();

    // Initialize inputs
    top->clk = 0;
    top->n_reset = 0;
    top->select = 0;

    // Get input file name
    if (argc == 2) {
        in_file_name = argv[1];
        cout << "Input file: " << in_file_name << endl;
    } else {
        cerr << "Usage: " << argv[0];
        cerr << " <input file name>" << endl;
        exit(1);
    }

#if VM_TRACE
    // If verilator was invoked with --trace argument enable VCD tracing
    cout << "Tracing enabled." << endl;
    VerilatedVcdC* tfp = NULL;
    const char* flag = Verilated::commandArgsPlusMatch("trace");
    string vcd_file_name = "";
    string base_in_file_name = "";

    // Set VCD file name
    if (in_file_name.find_last_of("\\/") != string::npos) {
        // input file name was a full path --> strip off base file name
        uint32_t start_of_file_name_str = in_file_name.find_last_of("\\/") + 1;
        base_in_file_name = in_file_name.substr(start_of_file_name_str);
        vcd_file_name = base_in_file_name + ".vcd";
    } else {
        vcd_file_name = in_file_name + ".vcd";
    }
    cout << "VCD file: " << vcd_file_name << endl;

    // Turn on Verilator tracing
    Verilated::traceEverOn(true);  // Verilator must compute traced signals
    tfp = new VerilatedVcdC;
    top->trace(tfp, 99);  // Trace 99 levels of hierarchy
    tfp->open(vcd_file_name.c_str());  // Open the dump file
#endif

    // Reset the DUT
    for (uint8_t i = 0; i < (NUM_RESET_CYCLES / 2); i++) {
        // Increment Time
        main_time++;

        // Toggle main clock
        if ((main_time % 2) == 0) {
            // Toggle clock
            top->clk = 1;
        } else {
            // Toggle clock
            top->clk = 0;
        }

        // Evaluate model
        top->eval();

#if VM_TRACE
        // Dump trace data for this cycle
        if (tfp) {
            tfp->dump(main_time);
        }
#endif
    }

    // Pull DUT out of reset
    top->n_reset = 1;

    // Open input file
    in_file.open(in_file_name);
    if (!in_file) {
        cerr << "ERROR: input file does not exist." << endl;
        exit(1);
    }

    // Simulate encrypting all values from the file
    while (!Verilated::gotFinish() && in_file) {
        // Increment Time
        main_time++;

        // Toggle main clock
        if ((main_time % 2) == 0) {
            // Verify Counter Results
            check_num++;
            printf("Checking results for test %d...\n", check_num);
            assert(count_1 == top->count_1 && \
                "ERROR: Incorrect value for count_1.");
            assert(count_2 == top->count_2 && \
                "ERROR: Incorrect value for count_2.");

            // Toggle clock
            top->clk = 1;

            // perform increment
            if (select) {
                count_1++;
            } else {
                count_2++;
            }
        } else {
            // Toggle clock
            top->clk = 0;

            // Load next inputs
            in_file >> input_select;

            if (in_file) {
                // Increment test number
                test_num++;
                printf("Loading inputs for test %d...\n", test_num);

                // load next select into DUT
                select = input_select[0] & 0x1;
                printf("select: %d\n", select);
                top->select = select;
            }
        }

        // Evaluate model
        top->eval();

#if VM_TRACE
        // Dump trace data for this cycle
        if (tfp) {
            tfp->dump(main_time);
        }
#endif
    }
    // Final model cleanup
    in_file.close();
    top->final();

    // Close trace if opened
#if VM_TRACE
    if (tfp) {
        tfp->close();
        tfp = NULL;
    }
#endif

    //  Coverage analysis (since test passed)
#if VM_COVERAGE
    Verilated::mkdir("logs");
    VerilatedCov::write("logs/coverage.dat");
#endif

    // Destroy model
    delete top;
    top = NULL;

    // Fin
    exit(0);
}
