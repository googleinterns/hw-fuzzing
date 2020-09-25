// TODO(ttrippel): add license

#include "hw/tb/cpp/inc/stdin_fuzz_tb.h"

#include <iostream>

STDINFuzzTb::STDINFuzzTb(int argc, char** argv)
    : VerilatorTb(argc, argv), test_num_(0) {}

STDINFuzzTb::~STDINFuzzTb() {}

bool STDINFuzzTb::ReadBytes(uint8_t* buffer, uint32_t num_bytes) {
  // Read num_bytes from input file stream into buffer
  if (!std::cin.eof()) {
    // Read file as a byte stream
    std::cin.read(reinterpret_cast<char*>(buffer), num_bytes);
    if (std::cin.gcount() < num_bytes) {
      return false;
    }
    // Increment test number
    test_num_++;
    return true;
  }
  return false;
}

// test
uint32_t STDINFuzzTb::get_test_num() { return test_num_; }
