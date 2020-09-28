// TODO(ttrippel): add license

#include "hw/tb/cpp/inc/tlul_host_tb.h"

#include <iomanip>
#include <iostream>

TLULHostTb::TLULHostTb(int argc, char** argv) : STDINFuzzTb(argc, argv) {
  // Initialize all bus signals to 0, except set host to ready to receive data
  ResetH2DSignals();
  SetH2DSignal(TL_D_READY_INDEX, TL_D_READY_WIDTH, 1);
}

TLULHostTb::~TLULHostTb() {}

uint32_t TLULHostTb::Get(uint32_t address) {
  // Send request and wait for response
  SendTLULRequest(OpcodeA::kPutFullData, address, 0, OT_TL_SZW, FULL_MASK);
  WaitForDeviceReady();

  // Unpack reponse
  uint32_t d_data = UnpackSignal(dut_.tl_o, TL_D_DATA_INDEX, TL_D_DATA_WIDTH);
  uint32_t d_opcode =
      UnpackSignal(dut_.tl_o, TL_D_OPCODE_INDEX, TL_D_OPCODE_WIDTH);
  uint32_t d_error =
      UnpackSignal(dut_.tl_o, TL_D_ERROR_INDEX, TL_D_ERROR_WIDTH);

  // TODO(ttrippel): RAISE ERROR
  // if (d_error || d_opcode != (uint32_t)OpcodeD::kAccessAckData) {
  //}

  return d_data;
}

uint32_t TLULHostTb::UnpackSignal(uint32_t* signals, uint32_t index,
                                  uint32_t width) {
  // Compute start/end word and bit indices of target value
  uint8_t start_word_ind = index / OT_TL_O_WORD_SIZE_BITS;
  uint8_t end_word_ind = (index + width - 1) / OT_TL_O_WORD_SIZE_BITS;
  uint8_t start_bit_index = index - (start_word_ind * OT_TL_O_WORD_SIZE_BITS);
  uint8_t end_bit_index =
      index + width - 1 - (end_word_ind * OT_TL_O_WORD_SIZE_BITS);
  uint32_t signal = 0;

  // If word indices are the same, signal bits resides in the same word,
  // otherwise, the bits straddle two words. Numeric values of individual TLUL
  // signals are unpacked by shifting and masking.
  if (start_word_ind == end_word_ind) {
    signal = signals[start_word_ind] >> start_bit_index;
    signal &= (1U << width) - 1;
  } else if ((end_word_ind - 1) == start_word_ind) {
    // Compute width of the low portion of the signal
    uint8_t low_width = OT_TL_O_WORD_SIZE_BITS - start_bit_index;

    // Shift THEN mask LOW subword
    uint32_t signal_low = signals[start_word_ind] >> start_bit_index;
    signal_low &= (1U << low_width) - 1;

    //  Mask THEN shift HIGH subword
    uint32_t high_mask = (1U << (end_bit_index + 1)) - 1;
    uint32_t signal_high = (signals[end_word_ind] & high_mask) << low_width;
    signal = signal_low | signal_high;
  }
  // TODO: RAISE ERROR
  // else {
  // continue;
  //}

  return signal;
}

void TLULHostTb::ClearRequestAfterDelay(uint32_t num_clk_cycles) {
  for (uint32_t i = 0; i < num_clk_cycles; i++) {
    ToggleClock(&dut_.clk_i, 2);
  }
  ResetH2DSignals();
  SetH2DSignal(TL_D_READY_INDEX, TL_D_READY_WIDTH, 1);
#ifdef DEBUG
  std::cout << "Clearing TL-UL request ..." << std::endl;
  PrintH2DSignals();
#endif
}

// TODO: complete this
void TLULHostTb::PrintD2HSignals() {
  std::cout << "+----------------------------+" << std::endl;
  std::cout << "|TL-UL Device-to-Host Signals|" << std::endl;
  std::cout << "+----------------+-----------+" << std::endl;
  std::cout << "|D_VALID         | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_D_VALID_INDEX, TL_D_VALID_WIDTH)
            << "|" << std::endl;
  std::cout << "|D_OPCODE        | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_D_OPCODE_INDEX, TL_D_OPCODE_WIDTH)
            << "|" << std::endl;
  std::cout << "|D_PARAM         | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_D_PARAM_INDEX, TL_D_PARAM_WIDTH)
            << "|" << std::endl;
  std::cout << "|D_SIZE          | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_D_SIZE_INDEX, TL_D_SIZE_WIDTH) << "|"
            << std::endl;
  std::cout << "|D_SOURCE        | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_D_SOURCE_INDEX, TL_D_SOURCE_WIDTH)
            << "|" << std::endl;
  std::cout << "|D_SINK          | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_D_SINK_INDEX, TL_D_SINK_WIDTH) << "|"
            << std::endl;
  std::cout << "|D_DATA          | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_D_DATA_INDEX, TL_D_DATA_WIDTH) << "|"
            << std::endl;
  std::cout << "|D_USER          | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_D_USER_INDEX, TL_D_USER_WIDTH) << "|"
            << std::endl;
  std::cout << "|D_ERROR         | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_D_ERROR_INDEX, TL_D_ERROR_WIDTH)
            << "|" << std::endl;
  std::cout << "|A_READY         | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_o, TL_A_READY_INDEX, TL_A_READY_WIDTH)
            << "|" << std::endl;
  std::cout << "+----------------+-----------+" << std::endl;
}

// TODO: complete this
void TLULHostTb::PrintH2DSignals() {
  std::cout << "+----------------------------+" << std::endl;
  std::cout << "|TL-UL Host-to-Device Signals|" << std::endl;
  std::cout << "+----------------+-----------+" << std::endl;
  std::cout << "|A_VALID         | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_i, TL_A_VALID_INDEX, TL_A_VALID_WIDTH)
            << "|" << std::endl;
  std::cout << "|A_OPCODE        | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_i, TL_A_OPCODE_INDEX, TL_A_OPCODE_WIDTH)
            << "|" << std::endl;
  std::cout << "|A_PARAM         | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_i, TL_A_PARAM_INDEX, TL_A_PARAM_WIDTH)
            << "|" << std::endl;
  std::cout << "|A_SIZE          | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_i, TL_A_SIZE_INDEX, TL_A_SIZE_WIDTH) << "|"
            << std::endl;
  std::cout << "|A_SOURCE        | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_i, TL_A_SOURCE_INDEX, TL_A_SOURCE_WIDTH)
            << "|" << std::endl;
  std::cout << "|A_ADDRESS       | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_i, TL_A_ADDRESS_INDEX, TL_A_ADDRESS_WIDTH)
            << "|" << std::endl;
  std::cout << "|A_DATA          | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_i, TL_A_DATA_INDEX, TL_A_DATA_WIDTH) << "|"
            << std::endl;
  std::cout << "|A_USER          | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_i, TL_A_USER_INDEX, TL_A_USER_WIDTH) << "|"
            << std::endl;
  std::cout << "|D_READY         | 0x" << std::setfill('0')
            << std::setw(OT_TL_DW >> 2) << std::hex
            << UnpackSignal(dut_.tl_i, TL_D_READY_INDEX, TL_D_READY_WIDTH)
            << "|" << std::endl;
  std::cout << "+----------------+-----------+" << std::endl;
}

// Performs PutFullData TileLink transaction.
void TLULHostTb::PutFull(uint32_t address, uint32_t data) {
  // TODO(ttrippel): add size and mask as input parameters and validate them.
  // Note: technically, the TL-UL spec. allows for full data writes for
  // registers smaller than the bus width, but OpenTitan documentation states
  // PutFullData operations should set a_size to full data bus width. This may
  // be because all IP registers are at word aligned addresses?

  // Send request and wait for response
  SendTLULRequest(OpcodeA::kPutFullData, address, data, OT_TL_SZW, FULL_MASK);
  ReceiveTLULPutResponse();
}

// Performs PutPartialData TileLink transaction.
void TLULHostTb::PutPartial(uint32_t address, uint32_t data, uint32_t size,
                            uint32_t mask) {
  // Validate size
  if (size > OT_TL_SZW) {
    // TODO: RAISE ERROR
    return;
  }

  // TODO(ttrippel): Validate address and mask match given size of transaction

  // Send request and wait for response
  SendTLULRequest(OpcodeA::kPutPartialData, address, data, size, mask);
  ReceiveTLULPutResponse();
}

// Receives a TL-UL Put or Put-Partial request reponse from a device.
void TLULHostTb::ReceiveTLULPutResponse() {
  // Wait for the response, then unpack opcode and error signals
  WaitForDeviceResponse();
  uint32_t d_opcode =
      UnpackSignal(dut_.tl_o, TL_D_OPCODE_INDEX, TL_D_OPCODE_WIDTH);
  uint32_t d_error =
      UnpackSignal(dut_.tl_o, TL_D_ERROR_INDEX, TL_D_ERROR_WIDTH);

  // Check if transaction failed
  // TODO(ttrippel): RAISE ERROR
  // if (d_error || d_opcode != OpcodeD::kAccessAck) {
  // continue;
  //}
}

// Resets all Host-to-Device signals' bits to 0
void TLULHostTb::ResetH2DSignals() {
  for (uint8_t i = 0; i < OT_TL_I_NUM_WORDS; i++) {
    dut_.tl_i[i] = 0;
  }
#ifdef DEBUG
  std::cout << "Resetting all Host-to-Device signals ..." << std::endl;
  PrintH2DSignals();
#endif
}

// Puts a TL-UL transaction request on the bus, waits for the device to signal
// it is ready to receive the request from the host, then waits one clock cycle
// before resetting all the host-to-device bus signals.
void TLULHostTb::SendTLULRequest(OpcodeA opcode, uint32_t address,
                                 uint32_t data, uint32_t size, uint32_t mask) {
  // Put request on the bus
  SetH2DSignal(TL_A_VALID_INDEX, TL_A_VALID_WIDTH, 1);
  SetH2DSignal(TL_A_OPCODE_INDEX, TL_A_OPCODE_WIDTH, (uint32_t)opcode);
  // SetH2DSignal(TL_A_SIZE_INDEX, TL_A_SIZE_WIDTH, size);
  // SetH2DSignal(TL_A_ADDRESS_INDEX, TL_A_ADDRESS_WIDTH, address);
  // SetH2DSignal(TL_A_DATA_INDEX, TL_A_DATA_WIDTH, data);
  // SetH2DSignal(TL_A_MASK_INDEX, TL_A_MASK_WIDTH, mask);
  // SetH2DSignal(TL_D_READY_INDEX, TL_D_READY_WIDTH, 1);
#ifdef DEBUG
  std::cout << "Putting TL-UL transaction on bus ..." << std::endl;
  PrintH2DSignals();
#endif
  exit(0);

  // Wait for request to be received by the device
  WaitForDeviceReady();
  ClearRequestAfterDelay(1);
}

// TODO: complete this
void TLULHostTb::SetH2DSignal(uint32_t index, uint32_t width, uint32_t value) {
  // Compute start/end word and bit indices of target value
  uint8_t start_word_ind = index / OT_TL_O_WORD_SIZE_BITS;
  uint8_t end_word_ind = (index + width - 1) / OT_TL_O_WORD_SIZE_BITS;
  uint8_t start_bit_index = index - (start_word_ind * OT_TL_O_WORD_SIZE_BITS);
  uint8_t end_bit_index =
      index + width - 1 - (end_word_ind * OT_TL_O_WORD_SIZE_BITS);

  // If word indices are the same, signal bits resides in the same word,
  // otherwise, the bits straddle two words. Individual TLUL signal values are
  // packed by clearing existing value bits and setting new value bits.
  if (start_word_ind == end_word_ind) {
    // clear existing signal value
    dut_.tl_i[start_word_ind] &= ~((1U << width) - 1) << start_bit_index;
    // set new signal value
    dut_.tl_i[start_word_ind] |= value << start_bit_index;
  } else if ((end_word_ind - 1) == start_word_ind) {
    // Operate on LOWER word
    // Compute width of the low portion of the signal
    uint8_t low_width = OT_TL_O_WORD_SIZE_BITS - start_bit_index;
    // Clear existing signal value
    dut_.tl_i[start_word_ind] &= ~((1U << low_width) - 1) << start_bit_index;
    // TODO: zero out upper bits of value that are shifted past width?
    dut_.tl_i[start_word_ind] |= value << start_bit_index;

    // Operate on UPPER word
    uint32_t high_mask = (1U << (end_bit_index + 1)) - 1;
    // Clear existing signal value
    dut_.tl_i[end_word_ind] &= ~((1U << (end_bit_index + 1)) - 1);
    // TODO: zero out lower bits of value that are shifted past width?
    dut_.tl_i[end_word_ind] |= value >> low_width;
  } else {
    // TODO: RAISE ERROR
  }
}

// Waits for the device to be ready to receive a host transaction request.
void TLULHostTb::WaitForDeviceReady() {
  while (!UnpackSignal(dut_.tl_o, TL_A_READY_INDEX, TL_A_READY_WIDTH)) {
    ToggleClock(&dut_.clk_i, 2);
  }
#ifdef DEBUG
  std::cout << "Device is ready!" << std::endl;
  PrintD2HSignals();
#endif
}

// Waits until the device transaction response is valid.
void TLULHostTb::WaitForDeviceResponse() {
  while (!UnpackSignal(dut_.tl_o, TL_D_VALID_INDEX, TL_D_VALID_WIDTH)) {
    ToggleClock(&dut_.clk_i, 2);
  }
#ifdef DEBUG
  std::cout << "Device response is valid!" << std::endl;
  PrintD2HSignals();
#endif
}
