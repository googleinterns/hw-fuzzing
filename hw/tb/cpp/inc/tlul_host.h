// TODO(ttrippel): add license

#ifndef HW_TB_CPP_INC_TLUL_HOST_H_
#define HW_TB_CPP_INC_TLUL_HOST_H_

#include <cmath>

#include "Vtop.h"
#include "verilated.h"

// TODO(ttrippel): make these auto-configurable, maybe by parsing SV package?
// -----------------------------------------------------------------------------
// OpenTitan TL-UL Bus Parameters (defined in opentitan/.../top_pkg.sv):
// -----------------------------------------------------------------------------
#define OT_TL_AW 32              // width of address bus in bits
#define OT_TL_DW 32              // width of data bus in bits
#define OT_TL_AIW 8              // width of address (host) source ID in bits
#define OT_TL_DIW 1              // width of (device) sink ID in bits
#define OT_TL_AUW 16             // width of host user bits (OT extension)
#define OT_TL_DUW 16             // width of device user bits (OT extension)
#define OT_TL_DBW OT_TL_DW >> 3  // # of data bytes in transaction (# mask bits)
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
#define TL_A_DATA_WIDTH OT_TL_DW
#define TL_A_USER_WIDTH OT_TL_AUW  // specific to OpenTitan TL-UL implementation
#define TL_D_READY_WIDTH 1

// Offsets
#define TL_A_VALID_INDEX 0
#define TL_A_OPCODE_INDEX (TL_A_VALID_INDEX + TL_A_VALID_WIDTH)
#define TL_A_PARAM_INDEX (TL_A_OPCODE_INDEX + TL_A_OPCODE_WIDTH)
#define TL_A_SIZE_INDEX (TL_A_PARAM_INDEX + TL_A_PARAM_WIDTH)
#define TL_A_SOURCE_INDEX (TL_A_SIZE_INDEX + TL_A_SIZE_WIDTH)
#define TL_A_ADDRESS_INDEX (TL_A_SOURCE_INDEX + TL_A_SOURCE_WIDTH)
#define TL_A_DATA_INDEX (TL_A_ADDRESS_INDEX + TL_A_ADDRESS_WIDTH)
#define TL_A_USER_INDEX (TL_A_DATA_INDEX + TL_A_DATA_WIDTH)
#define TL_D_READY_INDEX (TL_A_USER_INDEX + TL_A_USER_WIDTH)

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
#define TL_D_OPCODE_INDEX (TL_D_VALID_INDEX + TL_D_VALID_WIDTH)
#define TL_D_PARAM_INDEX (TL_D_OPCODE_INDEX + TL_D_OPCODE_WIDTH)
#define TL_D_SIZE_INDEX (TL_D_PARAM_INDEX + TL_D_PARAM_WIDTH)
#define TL_D_SOURCE_INDEX (TL_D_SIZE_INDEX + TL_D_SIZE_WIDTH)
#define TL_D_SINK_INDEX (TL_D_SOURCE_INDEX + TL_D_SOURCE_WIDTH)
#define TL_D_DATA_INDEX (TL_D_SINK_INDEX + TL_D_SINK_WIDTH)
#define TL_D_USER_INDEX (TL_D_DATA_INDEX + TL_D_DATA_WIDTH)
#define TL_D_ERROR_INDEX (TL_D_USER_INDEX + TL_D_USER_WIDTH)
#define TL_A_READY_INDEX (TL_D_ERROR_INDEX + TL_D_ERROR_WIDTH)

// -----------------------------------------------------------------------------
// Other defines
// -----------------------------------------------------------------------------
#define FULL_MASK ((1U << TL_DBW) - 1)
#define OT_TL_I_WORD_SIZE_BITS 32
#define OT_TL_O_WORD_SIZE_BITS 32
// TODO(ttrippel): compute these from above
#define OT_TL_I_NUM_WORDS 4
#define OT_TL_O_NUM_WORDS 3

// -----------------------------------------------------------------------------

enum class OpcodeA {
  kPutFullData = 0,
  kPutPartialData = 1,
  kGet = 4,
}

enum class OpcodeD {
  kAccessAsk = 0,
  kAccessAckData = 1,
}

class TLULHost : public STDINFuzzTb {
 public:
  TLULHost(vluint32_t* tl_h2d, vluint32_t* tl_d2h);
  ~TLULHost();
  void PutFull(uint32_t address, uint32_t data);
  void PutPartial(uint32_t address, uint32_t data, uint8_t size, uint8_t mask);
  uint32_t Get(uint32_t address);

 private:
  vluint32_t* tl_h2d_;
  vluint32_t* tl_d2h_;
  void WaitForDeviceReady();
  void ClearRequestAfterDelay(uint32_t num_clk_cycles);
  void WaitForDeviceResponse();
  void SendTLULRequest(OpcodeA opcode, uint32_t address, uint32_t data,
                       uint8_t size, uint8_t mask);
  void ReceiveTLULPutResponse();
  void SetH2DSignal(uint32_t index, uint32_t width, uint32_t value);
  void ResetH2DSignals();
  uint32_t UnpackSignal(uint32_t* signals, uint32_t index, uint32_t width);
  void PrintH2DSignals();
  void PrintD2HSignals();
}

#endif  // HW_TB_CPP_INC_TLUL_HOST_H_
