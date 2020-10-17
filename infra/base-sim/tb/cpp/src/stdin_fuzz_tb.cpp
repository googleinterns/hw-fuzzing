// Copyright 2020 Timothy Trippel
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
