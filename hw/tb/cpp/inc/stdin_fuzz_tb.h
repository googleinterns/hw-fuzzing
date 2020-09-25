// TODO(ttrippel): add license

#ifndef HW_TB_CPP_INC_STDIN_FUZZ_TB_H_
#define HW_TB_CPP_INC_STDIN_FUZZ_TB_H_

#include "hw/tb/cpp/inc/verilator_tb.h"

class STDINFuzzTb : public VerilatorTb {
 public:
  STDINFuzzTb(int argc, char** argv);
  ~STDINFuzzTb();
  bool ReadBytes(uint8_t* buffer, uint32_t num_bytes);
  uint32_t get_test_num();

 private:
  uint32_t test_num_;  // number of fuzz tests run read from STDIN
};

#endif  // HW_TB_CPP_INC_STDIN_FUZZ_TB_H_
