// TODO(ttrippel): add license

#include "hw/tb/cpp/inc/tlul_host.h"

TLULHost::TLULHost(Vtop* dut, vluint8_t* clk, vluint64_t main_time,
                   vluint32_t* tl_h2d, vluint32_t* tl_d2h)
    : dut_(dut),
      clk_(clock),
      main_time_(main_time),
      tl_h2d_(tl_h2d),
      tl_d2h_(tl_d2h) {
  // TODO(ttrippel): Initialize default values for bus
}

TLULHost::~TLULHost() {}

uint32_t TLULHost::Get(uint32_t address) {
  // Send request and wait for response
  SendTLULRequest(OpcodeA::kPutFullData, address, 0, OT_TL_SZW,
                  (2 * *OT_TL_DBW) - 1, sync);
  WaitForDeviceReady();

  // Unpack reponse
  uint32_t d_data = get_tl_d2h_(TL_D_DATA_INDEX, TL_D_DATA_WIDTH);
  uint32_t d_opcode = get_tl_d2h_(TL_D_OPCODE_INDEX, TL_D_OPCODE_WIDTH);
  uint32_t d_error = get_tl_d2h_(TL_D_ERROR_INDEX, TL_D_ERROR_WIDTH);

  if (d_error || d_opcode != OpcodeD::AccessAckData) {
    // TODO(ttrippel): RAISE ERROR
    continue;
  }

  return d_data;
}

uint32_t TLULHost::get_tl_d2h_(uint32_t index, uint32_t width) {
  return /* something */;
}

void TLULHost::ClearRequestAfterDelay(uint32_t num_clk_cycles) {}

void TLULHost::PrintTLSignals(uint32_t* signals, uint32_t num_bits) {}

void TLULHost::PutFull(uint32_t address, uint32_t data) {}

void TLULHost::PutPartial(uint32_t address, uint32_t data, uint8_t size,
                          uint8_t mask) {}

void TLULHost::ReceiveTLULPutResponse() {}

void TLULHost::SendTLULRequest(OpcodeA opcode, uint32_t address, uint32_t data,
                               uint8_t size, uint8_t mask) {
  // Put request on the bus
  set_tl_h2d_(TL_A_VALID_INDEX, TL_A_VALID_WIDTH, 1);
  set_tl_h2d_(TL_A_OPCODE_INDEX, TL_A_OPCODE_WIDTH, (uint32_t)opcode);
  set_tl_h2d_(TL_A_SIZE_INDEX, TL_A_SIZE_WIDTH, size);
  set_tl_h2d_(TL_A_ADDRESS_INDEX, TL_A_ADDRESS_WIDTH, address);
  set_tl_h2d_(TL_A_DATA_INDEX, TL_A_DATA_WIDTH, data);
  set_tl_h2d_(TL_A_MASK_INDEX, TL_A_MASK_WIDTH, mask);
  set_tl_h2d_(TL_A_READY_INDEX, TL_A_READY_WIDTH, 1);

  // Wait for request to be received by the device
  WaitForDeviceReady();
  ClearRequestAfterDelay(1);
}

void TLULHost::set_tl_h2d_(uint32_t index, uint32_t width, uint32_t value) {}

void TLULHost::WaitForDeviceReady() {}

void TLULHost::WaitForDeviceReady() {}
