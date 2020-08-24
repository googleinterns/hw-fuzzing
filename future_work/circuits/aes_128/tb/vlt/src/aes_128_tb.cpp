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

#include <aes_128_tb.h>

#include <cstdlib>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <string>
#include <list>

// CryptoPP Library
#include "cryptopp/modes.h"
#include "cryptopp/aes.h"
#include "cryptopp/filters.h"
#include "cryptopp/hex.h"
using CryptoPP::AES;
using CryptoPP::ECB_Mode;
using CryptoPP::Exception;
using CryptoPP::HexEncoder;
using CryptoPP::StringSink;
using CryptoPP::StreamTransformationFilter;
using CryptoPP::StringSource;
//using std::cerr;
//using std::cout;
//using std::endl;
//using std::fstream;
//using std::hex;
//using std::list;
//using std::setfill;
//using std::setw;
//using std::string;

// Testbench Parameters
#define PIPELINE_DEPTH 20

// Constructor
AES128Tb::AES128Tb(int argc, char** argv)
    : num_checks_(0),
      main_time_(0),
      dut_(),
      tb_(INPUT_PORT_SIZE_BYTES, argc, argv)
#if VM_TRACE
      ,
      tracing_file_pointer_(NULL),
      vcd_file_name_("")
#endif
{
#if VM_TRACE
    InitializeTracing(argv[1]);
#endif

// Destructor
AES128Tb::~AES128Tb() {
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
void AES128Tb::InitializeTracing(std::string fname) {
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
void AES128Tb::InitializeDUT() {
    dut_.clk = 0;
    dut_.state[0] = 0;
    dut_.state[1] = 0;
    dut_.state[2] = 0;
    dut_.state[3] = 0;
    dut_.key[0] = 0;
    dut_.key[1] = 0;
    dut_.key[2] = 0;
    dut_.key[3] = 0;
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
void AES128Tb::ToggleClock(uint32_t num_toggles) {
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

// Simulate the DUT with testbench input file
void AES128Tb::SimulateDUT() {
    // Create buffer for test data
    uint8_t test_input[INPUT_PORT_SIZE_BYTES] = {0};

    // Read tests and simulate DUT
    while (test_.ReadTest(test_input) && !Verilated::gotFinish()) {
        // Load test into DUT
        dut_.code = (test_input[0]);

        // Print test read from file
        std::cout << "Loading inputs for test " << test_.get_test_num();
        std::cout << " (time = " << unsigned(main_time_) << ") ...";
        std::cout << std::endl;
        std::cout << "  in = " << std::bitset<8>(test_input[0]);
        std::cout << " (0x" << std::hex << unsigned(test_input[0]) << ")";
        std::cout << std::endl;
        std::cout << "  dut.code = " << std::bitset<8>(dut_.code);
        std::cout << " (0x" << std::hex << unsigned(dut_.code) << ")";
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

    // Reset the DUT --> no reset for this core (its purely combinational)

    // Simulate the DUT
    tb.SimulateDUT();
}








// Current simulation time (64-bit unsigned)
vluint64_t main_time = 0;

// Called by $time in Verilog
double sc_time_stamp() {
    return main_time;  // Note does conversion to real, to match SystemC
}

// Print hex values of an array of bytes
void print_bytes_hex(uint8_t* bytes, uint32_t num_bytes) {
    for (uint32_t i = 0; i < num_bytes; i++) {
        cout << setfill('0') << setw(2);
        cout << hex << (0xFF & bytes[i]);
    }
}

// Print hex values of chars in a string
void print_string_hex(string s) {
    for (uint32_t i = 0; i < s.length(); i++) {
        cout << setfill('0') << setw(2);
        cout << hex << (0xFF & s[i]);
    }
}

// Check AES encryption output is correct using Crypto++ Lib
bool check_aes_128_encryption(\
        string key, \
        string state, \
        uint8_t* out_bytes) {
    // Print Key
    cout << "Encryption Key:   ";
    print_string_hex(key);
    cout << endl;

    // Print State
    cout << "Encryption State: ";
    print_string_hex(state);
    cout << endl;

    // Print Out
    cout << "Encryption Out:   ";
    print_bytes_hex(out_bytes, STATE_SIZE);
    cout << endl;

    // Load Key
    ECB_Mode<AES>::Encryption cipher;
    cipher.SetKey((const uint8_t*) key.c_str(), key.length());

    // Create Cipher Text
    string ciphertext;
    try {
        StringSource(state, true, \
                new StreamTransformationFilter(cipher, \
                    new StringSink(ciphertext), \
                    StreamTransformationFilter::NO_PADDING));
    }
    catch(const Exception& cipher) {
        cerr << cipher.what() << endl;
        exit(1);
    }

    // Print Correct Cipher Text
    cout << "Correct Out:      ";
    print_string_hex(ciphertext);
    cout << endl;
    cout << endl;

    // Check encryption results
    if (memcmp(out_bytes, ciphertext.c_str(), ciphertext.length()) == 0) {
        return true;
    }

    return false;
}

int main(int argc, char** argv, char** env) {
    // Test Bench Inputs
    fstream in_file;
    uint32_t test_num = 0;
    uint32_t check_num = 0;
    list<string> keys;
    list<string> states;
    string in_file_name = "";
    string input_key = "";
    string input_state = "";
    uint8_t one_byte = 0;
    uint8_t out_bytes [STATE_SIZE] = {};

    // Set debug level, 0 is off, 9 is highest presently used
    // May be overridden by commandArgs
    Verilated::debug(0);

    // Randomization reset policy
    // May be overridden by commandArgs
    Verilated::randReset(2);

    // Pass arguments so Verilated code can see them, e.g. $value$plusargs
    // This needs to be called before you create any model
    Verilated::commandArgs(argc, argv);

    // Construct the Verilated model, from Vaes_128.h
    // generated from Verilating "aes_128.v"
    Vaes_128* top = new Vaes_128();

    // Initialize AES inputs
    top->clk = 0;
    top->state[0] = 0;
    top->state[1] = 0;
    top->state[2] = 0;
    top->state[3] = 0;
    top->key[0] = 0;
    top->key[1] = 0;
    top->key[2] = 0;
    top->key[3] = 0;

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

    // Open input file
    in_file.open(in_file_name);
    if (!in_file) {
        cerr << "ERROR: input file does not exist." << endl;
        exit(1);
    }

    // Simulate encrypting all values from the file
    while (!Verilated::gotFinish() && (in_file || keys.size() > 0)) {
        // Increment Time
        main_time++;

        // Toggle AES main clock
        if ((main_time % 2) == 0) {
            // Toggle clock
            top->clk = 1;
        } else {
            // Toggle clock
            top->clk = 0;

            // Verify Encryption Results
            if ((main_time / 2) > PIPELINE_DEPTH) {
                // Increment test check number
                check_num++;
                printf("Checking results for test %d...\n", check_num);

                // Convert output to byte array
                for (int i = 0; i < 4; i++) {
                    for (uint8_t j = 0; j < 4; j++) {
                        one_byte = top->out[3 - i] >> ((3 - j) * 8);
                        out_bytes[(i * 4) + j] = 0xFF & one_byte;
                    }
                }

                assert(check_aes_128_encryption(\
                            keys.front(), \
                            states.front(), \
                            out_bytes) && "ERROR: encryption is wrong!\n");
                keys.pop_front();
                states.pop_front();
            }

            // Load next key and state
            in_file >> input_key;
            in_file >> input_state;

            if (in_file) {
                // Increment test number
                test_num++;
                printf("Loading key and state for test %d...\n", test_num);

                // load next aes key into DUT
                cout << "key: " << input_key << endl;
                keys.push_back(input_key);
                for (int i = 3; i >= 0; i--) {
                    for (uint8_t j = 0; j < 4; j++) {
                        one_byte = input_key[((3 - i) * 4) + j];
                        top->key[i] = (top->key[i] << 8) | one_byte;
                    }
                }

                // load next aes state into DUT
                cout << "state: " << input_state << endl;
                states.push_back(input_state);
                for (int i = 3; i >= 0; i--) {
                    for (uint8_t j = 0; j < 4; j++) {
                        one_byte = input_state[((3 - i) * 4) + j];
                        top->state[i] = (top->state[i] << 8) | one_byte;
                    }
                }
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
