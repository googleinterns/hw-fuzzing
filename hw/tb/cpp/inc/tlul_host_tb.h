// TODO(ttrippel): add license

#ifndef HW_TB_CPP_INC_TLUL_HOST_TB_H_
#define HW_TB_CPP_INC_TLUL_HOST_TB_H_

#include <cmath>

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
#define TL_A_VALID_INDEX 0
#define TL_A_OPCODE_INDEX 1
#define TL_A_PARAM_INDEX 4
#define TL_A_SIZE_INDEX 7
#define TL_A_SOURCE_INDEX 9
#define TL_A_ADDRESS_INDEX 17
#define TL_A_MASK_INDEX 49
#define TL_A_DATA_INDEX 53
#define TL_A_USER_INDEX 85
#define TL_D_READY_INDEX 101

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
#define TL_D_VALID_INDEX 0
#define TL_D_OPCODE_INDEX 1
#define TL_D_PARAM_INDEX 4
#define TL_D_SIZE_INDEX 7
#define TL_D_SOURCE_INDEX 9
#define TL_D_SINK_INDEX 17
#define TL_D_DATA_INDEX 18
#define TL_D_USER_INDEX 50
#define TL_D_ERROR_INDEX 66
#define TL_A_READY_INDEX 67

// -----------------------------------------------------------------------------
// Other defines
// -----------------------------------------------------------------------------
#define FULL_MASK ((1U << OT_TL_DBW) - 1)
#define OT_TL_I_WORD_SIZE_BITS 32
#define OT_TL_O_WORD_SIZE_BITS 32
#define OT_TL_I_NUM_WORDS 4
#define OT_TL_O_NUM_WORDS 3
#define LINE_SEP "============================================================="
#define DEBUG

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
  void PutFull(uint32_t address, uint32_t data);
  void PutPartial(uint32_t address, uint32_t data, uint32_t size,
                  uint32_t mask);
  uint32_t Get(uint32_t address);

 private:
  void WaitForDeviceReady();
  void ClearRequestAfterDelay(uint32_t num_clk_cycles);
  void WaitForDeviceResponse();
  void SendTLULRequest(OpcodeA opcode, uint32_t address, uint32_t data,
                       uint32_t size, uint32_t mask);
  void ReceiveTLULPutResponse();
  void SetH2DSignal(uint32_t index, uint32_t width, uint32_t value);
  void ResetH2DSignals();
  uint32_t UnpackSignal(uint32_t* signals, uint32_t index, uint32_t width);
  void PrintH2DSignals();
  void PrintD2HSignals();
};

#endif  // HW_TB_CPP_INC_TLUL_HOST_TB_H_
