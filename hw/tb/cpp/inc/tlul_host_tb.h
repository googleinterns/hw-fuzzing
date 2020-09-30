// TODO(ttrippel): add license

#ifndef HW_TB_CPP_INC_TLUL_HOST_TB_H_
#define HW_TB_CPP_INC_TLUL_HOST_TB_H_

#include <cmath>
#include <unordered_map>
#include <vector>

#include "Vtop.h"
#include "hw/tb/cpp/inc/stdin_fuzz_tb.h"
#include "verilated.h"

// TODO(ttrippel): make these auto-configurable, maybe by parsing SV package?
// -----------------------------------------------------------------------------
// OpenTitan TL-UL Bus Parameters (defined in opentitan/.../top_pkg.sv):
// -----------------------------------------------------------------------------
#define OT_TL_AW 32                // width of address bus in bits
#define OT_TL_DW 32                // width of data bus in bits
#define OT_TL_AIW 8                // width of address (host) source ID in bits
#define OT_TL_DIW 1                // width of (device) sink ID in bits
#define OT_TL_AUW 16               // width of host user bits (OT extension)
#define OT_TL_DUW 16               // width of device user bits (OT extension)
#define OT_TL_DBW (OT_TL_DW >> 3)  // data bus width in # of bytes (# mask bits)
#define OT_TL_SZW ceil(log2(OT_TL_DBW))  // setting for size A_SIZE/D_SIZE

// -----------------------------------------------------------------------------
// TL Host-to-Device signal widths & indices into struct packed signal: tl_i
// -----------------------------------------------------------------------------
// Widths
#define TL_A_VALID_WIDTH 1
#define TL_A_OPCODE_WIDTH 3
#define TL_A_PARAM_WIDTH 3
#define TL_A_SIZE_WIDTH OT_TL_SZW
#define TL_A_SOURCE_WIDTH OT_TL_AIW
#define TL_A_ADDRESS_WIDTH OT_TL_AW
#define TL_A_MASK_WIDTH OT_TL_DBW
#define TL_A_DATA_WIDTH OT_TL_DW
#define TL_A_USER_WIDTH OT_TL_AUW  // specific to OpenTitan TL-UL implementation
#define TL_D_READY_WIDTH 1

// Indices
#define TL_A_VALID_INDEX 101
#define TL_A_OPCODE_INDEX 98
#define TL_A_PARAM_INDEX 95
#define TL_A_SIZE_INDEX 93
#define TL_A_SOURCE_INDEX 85
#define TL_A_ADDRESS_INDEX 53
#define TL_A_MASK_INDEX 49
#define TL_A_DATA_INDEX 17
#define TL_A_USER_INDEX 1
#define TL_D_READY_INDEX 0

// -----------------------------------------------------------------------------
// TL Device-to-Host signal widths & indices into struct packed signal: tl_o
// -----------------------------------------------------------------------------
// Widths
#define TL_D_VALID_WIDTH 1
#define TL_D_OPCODE_WIDTH 3
#define TL_D_PARAM_WIDTH 3
#define TL_D_SIZE_WIDTH OT_TL_SZW
#define TL_D_SOURCE_WIDTH OT_TL_AIW
#define TL_D_SINK_WIDTH OT_TL_DIW
#define TL_D_DATA_WIDTH OT_TL_DW
#define TL_D_USER_WIDTH OT_TL_DUW  // specific to OpenTitan TL-UL implementation
#define TL_D_ERROR_WIDTH 1
#define TL_A_READY_WIDTH 1

// Indices
#define TL_D_VALID_INDEX 67
#define TL_D_OPCODE_INDEX 64
#define TL_D_PARAM_INDEX 61
#define TL_D_SIZE_INDEX 59
#define TL_D_SOURCE_INDEX 51
#define TL_D_SINK_INDEX 50
#define TL_D_DATA_INDEX 18
#define TL_D_USER_INDEX 2
#define TL_D_ERROR_INDEX 1
#define TL_A_READY_INDEX 0

// -----------------------------------------------------------------------------
// Other defines
// -----------------------------------------------------------------------------
#define FULL_MASK ((1U << OT_TL_DBW) - 1)
#define ONE_CLK_CYCLE 2
#define OT_TL_I_WORD_SIZE_BITS 32
#define OT_TL_O_WORD_SIZE_BITS 32
#define OT_TL_I_NUM_WORDS 4
#define OT_TL_O_NUM_WORDS 3
#define LINE_SEP "============================================================="

// -----------------------------------------------------------------------------
// Packed signal table macros
// -----------------------------------------------------------------------------
#define PACKED_SIGNAL_TABLE_BORDER_TOP                                         \
  "+-------------------------------------------------------------------------" \
  "+"
#define PACKED_SIGNAL_TABLE_COL_BORDER                                         \
  "+---------+-------+-------+-----------+-----------------------------------" \
  "+"
#define PACKED_SIGNAL_TABLE_COL_HEADER                                         \
  "| Signal  | Width | Index |    Hex    |                Binary             " \
  "|"

// -----------------------------------------------------------------------------
// Debug macros
// -----------------------------------------------------------------------------
//#define DEBUG
#define DEBUG_MSG(msg) std::cout << (msg) << std::endl;
#define DEBUG_VAL(name, x) std::cout << (name) << ": " << (x) << std::endl;

// -----------------------------------------------------------------------------

enum class OpcodeA {
  kPutFullData = 0,
  kPutPartialData = 1,
  kGet = 4,
};

enum class OpcodeD {
  kAccessAck = 0,
  kAccessAckData = 1,
};

class TLULHostTb : public STDINFuzzTb {
 public:
  TLULHostTb(int argc, char** argv);
  ~TLULHostTb();

  // TL-UL transaction methods
  bool PutFull(uint32_t address, uint32_t data);
  bool PutPartial(uint32_t address, uint32_t data, uint32_t size,
                  uint32_t mask);
  uint32_t Get(uint32_t address);

 private:
  // Signals specific to OpenTitan TL-UL bus implementation
  const std::vector<std::string> h2d_signals_{
      "A_VALID",   "A_OPCODE", "A_PARAM", "A_SIZE", "A_SOURCE",
      "A_ADDRESS", "A_MASK",   "A_DATA",  "A_USER", "D_READY"};
  const std::vector<std::string> d2h_signals_{
      "D_VALID", "D_OPCODE", "D_PARAM", "D_SIZE",  "D_SOURCE",
      "D_SINK",  "D_DATA",   "D_USER",  "D_ERROR", "A_READY"};
  const std::unordered_map<std::string, uint32_t> signal2index_ = {
      // Host-to-Device Signals
      {"A_VALID", TL_A_VALID_INDEX},
      {"A_OPCODE", TL_A_OPCODE_INDEX},
      {"A_PARAM", TL_A_PARAM_INDEX},
      {"A_SIZE", TL_A_SIZE_INDEX},
      {"A_SOURCE", TL_A_SOURCE_INDEX},
      {"A_ADDRESS", TL_A_ADDRESS_INDEX},
      {"A_MASK", TL_A_MASK_INDEX},
      {"A_DATA", TL_A_DATA_INDEX},
      {"A_USER", TL_A_USER_INDEX},
      {"D_READY", TL_D_READY_INDEX},
      // Device-to-Host Signals
      {"D_VALID", TL_D_VALID_INDEX},
      {"D_OPCODE", TL_D_OPCODE_INDEX},
      {"D_PARAM", TL_D_PARAM_INDEX},
      {"D_SIZE", TL_D_SIZE_INDEX},
      {"D_SOURCE", TL_D_SOURCE_INDEX},
      {"D_SINK", TL_D_SINK_INDEX},
      {"D_DATA", TL_D_DATA_INDEX},
      {"D_USER", TL_D_USER_INDEX},
      {"D_ERROR", TL_D_ERROR_INDEX},
      {"A_READY", TL_A_READY_INDEX}};
  const std::unordered_map<std::string, uint32_t> signal2width_ = {
      // Host-to-Device Signals
      {"A_VALID", TL_A_VALID_WIDTH},
      {"A_OPCODE", TL_A_OPCODE_WIDTH},
      {"A_PARAM", TL_A_PARAM_WIDTH},
      {"A_SIZE", TL_A_SIZE_WIDTH},
      {"A_SOURCE", TL_A_SOURCE_WIDTH},
      {"A_ADDRESS", TL_A_ADDRESS_WIDTH},
      {"A_MASK", TL_A_MASK_WIDTH},
      {"A_DATA", TL_A_DATA_INDEX},
      {"A_USER", TL_A_USER_WIDTH},
      {"D_READY", TL_D_READY_WIDTH},
      // Device-to-Host Signals
      {"D_VALID", TL_D_VALID_WIDTH},
      {"D_OPCODE", TL_D_OPCODE_WIDTH},
      {"D_PARAM", TL_D_PARAM_WIDTH},
      {"D_SIZE", TL_D_SIZE_WIDTH},
      {"D_SOURCE", TL_D_SOURCE_WIDTH},
      {"D_SINK", TL_D_SINK_WIDTH},
      {"D_DATA", TL_D_DATA_WIDTH},
      {"D_USER", TL_D_USER_WIDTH},
      {"D_ERROR", TL_D_ERROR_WIDTH},
      {"A_READY", TL_A_READY_WIDTH}};

  // TL-UL transaction helper methods
  bool WaitForDeviceReady();
  bool ClearRequestAfterDelay(uint32_t num_clk_cycles);
  bool WaitForDeviceResponse();
  bool SendTLULRequest(OpcodeA opcode, uint32_t address, uint32_t data,
                       uint32_t size, uint32_t mask);
  bool ReceiveTLULPutResponse();
  void SetH2DSignal(std::string signal_name, uint32_t value);
  void ResetH2DSignals();
  uint32_t UnpackSignal(uint32_t* packed_signals, std::string signal_name);
  void PrintSignalValue(uint32_t* packed_signals, std::string signal_name);
  void PrintH2DSignals();
  void PrintD2HSignals();
};

#endif  // HW_TB_CPP_INC_TLUL_HOST_TB_H_
