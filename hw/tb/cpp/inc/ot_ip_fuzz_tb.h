// TODO(ttrippel): add license

#ifndef HW_TB_CPP_INC_OT_IP_FUZZ_TB_H_
#define HW_TB_CPP_INC_OT_IP_FUZZ_TB_H_

#include "hw/tb/cpp/inc/tlul_host_tb.h"
#include "hw/tb/cpp/inc/verilator_tb.h"

#define ADDRESS_SIZE_BYTES_ENV_VAR "ADDRESS_SIZE"
#define DATA_SIZE_BYTES_ENV_VAR "DATA_SIZE"
#define OPCODE_SIZE_BYTES 1  // number of opcode bytes to read from STDIN
#define WAIT_OPCODE_THRESHOLD 85
#define RW_OPCODE_THRESHOLD 170
#define NUM_RESET_CLK_PERIODS 1

enum class HWFuzzOpcode {
  kInvalid = 0,
  kWait = 1,
  kRead = 2,
  kWrite = 3,
};

struct TLULAddress {
  bool valid;
  uint32_t address;
};

struct TLULData {
  bool valid;
  uint32_t data;
};

class OTIPFuzzTb : public TLULHostTb {
 public:
  OTIPFuzzTb(int argc, char** argv);
  ~OTIPFuzzTb();
  void SimulateDUT();

 private:
  void InitializeDUT();
  HWFuzzOpcode GetFuzzerOpcode();
  TLULAddress GetTLULAddress();
  TLULData GetTLULData();
  uint32_t address_size_bytes_;  // size of TL-UL address bus
  uint32_t data_size_bytes_;     // size of TL-UL data bus
};

#endif  // HW_TB_CPP_INC_OT_IP_FUZZ_TB_H_
