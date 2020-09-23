// TODO(ttrippel): add license

#ifndef HW_TB_CPP_INC_TLUL_FUZZ_TB_H_
#define HW_TB_CPP_INC_TLUL_FUZZ_TB_H_

#include "hw/tb/cpp/inc/verilator_tb.h"

// DUT parameters
#define OPCODE_SIZE_BYTES 1  // number of opcode bytes to read from STDIN
#define WAIT_OPCODE_THRESHOLD 85
#define RW_OPCODE_THRESHOLD 170
#define NUM_RESET_PERIODS 1

enum class HWFuzzOpcode {
  kWait = 0,
  kRead = 1,
  kWrite = 2,
};

class OTIPFuzzTb : public VerilatorTb {
 public:
  explicit OTIPFuzzTb(int argc, char** argv);
  ~OTIPFuzzTb();
  void ResetDUT();
  void SimulateDUT();

 private:
  void InitializeDUT();
  void ToggleClock(uint32_t num_toggles);
  uint8_t GetFuzzerOpcode();
  uint32_t GetTLULAddress();
  uint32_t GetTLULData();
  TLULDriver bus_driver_;            // TL-UL bus driver
  const uint32_t kAddressSizeBytes;  // size of TL-UL address bus
  const uint32_t kDataSizeBytes;     // size of TL-UL data bus
}

#endif  // HW_TB_CPP_INC_TLUL_FUZZ_TB_H_
