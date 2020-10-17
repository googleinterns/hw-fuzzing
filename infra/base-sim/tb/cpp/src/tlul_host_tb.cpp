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

#include "hw/tb/cpp/inc/tlul_host_tb.h"

#include <iomanip>
#include <iostream>

TLULHostTb::TLULHostTb(int argc, char** argv) : STDINFuzzTb(argc, argv) {
  // Initialize all bus signals to 0, except set host to ready to receive data
  ResetH2DSignals();
  SetH2DSignal("D_READY", 1);
#ifdef DEBUG
  std::cout << "Setting TL-UL host to ready!" << std::endl;
  PrintH2DSignals();
#endif
}

TLULHostTb::~TLULHostTb() {}

uint32_t TLULHostTb::Get(uint32_t address) {
  // Send request and wait for response
  if (SendTLULRequest(OpcodeA::kGet, address, 0, OT_TL_SZW, FULL_MASK) ||
      WaitForDeviceResponse()) {
    return ~0U;
  }

  // Unpack reponse
  uint32_t d_data = UnpackSignal(dut_.tl_o, "D_DATA");
  uint32_t d_opcode = UnpackSignal(dut_.tl_o, "D_OPCODE");
  uint32_t d_error = UnpackSignal(dut_.tl_o, "D_ERROR");

  // TODO(ttrippel): RAISE ERROR
  // if (d_error || d_opcode != (uint32_t)OpcodeD::kAccessAckData) {
  //}

  return d_data;
}

bool TLULHostTb::ClearRequestAfterDelay(uint32_t num_clk_cycles) {
  for (uint32_t i = 0; i < num_clk_cycles; i++) {
    if (ToggleClock(&dut_.clk_i, 2)) {
      return true;
    }
  }
  ResetH2DSignals();
  SetH2DSignal("D_READY", 1);
#ifdef DEBUG
  std::cout << "Clearing TL-UL request ..." << std::endl;
  PrintH2DSignals();
#endif
  return false;
}

// Prints a row in the H2D or D2H tables
void TLULHostTb::PrintSignalValue(uint32_t* packed_signals,
                                  std::string signal_name) {
  uint32_t signal_value = UnpackSignal(packed_signals, signal_name);
  const uint32_t signal_width = signal2width_.at(signal_name);
  std::cout << "|";
  std::cout << std::left << std::setfill(' ') << std::setw(9) << signal_name;
  std::cout << "|";
  std::cout << std::right << std::setw(7) << signal_width;
  std::cout << "|";
  std::cout << std::setw(7) << signal2index_.at(signal_name);
  std::cout << "|";
  std::cout << " 0x" << std::right << std::setfill('0') << std::setw(8)
            << std::hex << signal_value;
  std::cout << "|";
  std::cout << " " << std::setfill(' ') << std::setw(34 - signal_width)
            << std::dec << "b'";
  uint32_t current_bit = 1;
  uint32_t current_bitmask = 1U << (signal_width - 1);
  for (uint32_t i = 0; i < signal_width; i++) {
    current_bit = (signal_value & current_bitmask);
    current_bit >>= (signal_width - 1);
    std::cout << current_bit;
    signal_value <<= 1;
  }
  std::cout << "|" << std::endl;
}

// Prints unpacked values of Device-to-Host signals
void TLULHostTb::PrintD2HSignals() {
  std::cout << PACKED_SIGNAL_TABLE_BORDER_TOP << std::endl;
  std::cout << "|                   TL-UL Device-to-Host Signals (tl_o)        "
               "           |"
            << std::endl;
  std::cout << PACKED_SIGNAL_TABLE_COL_BORDER << std::endl;
  std::cout << PACKED_SIGNAL_TABLE_COL_HEADER << std::endl;
  std::cout << PACKED_SIGNAL_TABLE_COL_BORDER << std::endl;
  for (uint32_t i = 0; i < d2h_signals_.size(); i++) {
    PrintSignalValue(dut_.tl_o, d2h_signals_[i]);
  }
  std::cout << PACKED_SIGNAL_TABLE_COL_BORDER << std::endl;
}

// Prints unpacked values of Host-to-Device signals
void TLULHostTb::PrintH2DSignals() {
  std::cout << PACKED_SIGNAL_TABLE_BORDER_TOP << std::endl;
  std::cout << "|                   TL-UL Host-to-Device Signals (tl_i)        "
               "           |"
            << std::endl;
  std::cout << PACKED_SIGNAL_TABLE_COL_BORDER << std::endl;
  std::cout << PACKED_SIGNAL_TABLE_COL_HEADER << std::endl;
  std::cout << PACKED_SIGNAL_TABLE_COL_BORDER << std::endl;
  for (uint32_t i = 0; i < h2d_signals_.size(); i++) {
    PrintSignalValue(dut_.tl_i, h2d_signals_[i]);
  }
  std::cout << PACKED_SIGNAL_TABLE_COL_BORDER << std::endl;
}

// Performs PutFullData TileLink transaction.
bool TLULHostTb::PutFull(uint32_t address, uint32_t data) {
  // TODO(ttrippel): add size and mask as input parameters and validate them.
  // Note: technically, the TL-UL spec. allows for full data writes for
  // registers smaller than the bus width, but OpenTitan documentation states
  // PutFullData operations should set a_size to full data bus width. This may
  // be because all IP registers are at word aligned addresses?

  // Send request and wait for response
  if (SendTLULRequest(OpcodeA::kPutFullData, address, data, OT_TL_SZW,
                      FULL_MASK) ||
      ReceiveTLULPutResponse()) {
    return true;
  }
  return false;
}

// Performs PutPartialData TileLink transaction.
bool TLULHostTb::PutPartial(uint32_t address, uint32_t data, uint32_t size,
                            uint32_t mask) {
  // TODO(ttrippel): Validate size
  // if (size > OT_TL_SZW) {
  // RAISE ERROR
  // return false;
  //}

  // TODO(ttrippel): Validate address and mask match given size of transaction

  // Send request and wait for response
  if (SendTLULRequest(OpcodeA::kPutPartialData, address, data, size, mask) ||
      ReceiveTLULPutResponse()) {
    return true;
  }
  return false;
}

// Receives a TL-UL Put or Put-Partial request reponse from a device.
bool TLULHostTb::ReceiveTLULPutResponse() {
  // Wait for the response, then unpack opcode and error signals
  if (WaitForDeviceResponse()) {
    return true;
  }
  uint32_t d_opcode = UnpackSignal(dut_.tl_o, "D_OPCODE");
  uint32_t d_error = UnpackSignal(dut_.tl_o, "D_ERROR");

  // Check if transaction failed
  // TODO(ttrippel): RAISE ERROR
  // if (d_error || d_opcode != OpcodeD::kAccessAck) {
  // continue;
  //}
  return false;
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
// it is ready to receive the request from the host, then waits one clock
// cycle before resetting all the host-to-device bus signals.
bool TLULHostTb::SendTLULRequest(OpcodeA opcode, uint32_t address,
                                 uint32_t data, uint32_t size, uint32_t mask) {
  // Put request on the bus
  SetH2DSignal("A_VALID", 1);
  SetH2DSignal("A_OPCODE", (uint32_t)opcode);
  SetH2DSignal("A_SIZE", size);
  SetH2DSignal("A_ADDRESS", address);
  SetH2DSignal("A_DATA", data);
  SetH2DSignal("A_MASK", mask);
  SetH2DSignal("D_READY", 1);
#ifdef DEBUG
  std::cout << "Putting TL-UL transaction on bus ..." << std::endl;
  PrintH2DSignals();
#endif

  // Wait for request to be received by the device
  if (WaitForDeviceReady()) {
    return true;
  }
  if (ClearRequestAfterDelay(1)) {
    return true;
  }
  return false;
}

// Sets the given TL-UL signal name with the given value
void TLULHostTb::SetH2DSignal(std::string signal_name, uint32_t value) {
  // Compute start/end word and bit indices of target value
  uint32_t index = signal2index_.at(signal_name);
  uint32_t width = signal2width_.at(signal_name);
  uint8_t start_word_ind = index / OT_TL_O_WORD_SIZE_BITS;
  uint8_t end_word_ind = (index + width - 1) / OT_TL_O_WORD_SIZE_BITS;
  uint8_t start_bit_ind = index - (start_word_ind * OT_TL_O_WORD_SIZE_BITS);
  uint8_t end_bit_ind =
      index + width - 1 - (end_word_ind * OT_TL_O_WORD_SIZE_BITS);

  // If word indices are the same, signal bits resides in the same word,
  // otherwise, the bits straddle two words. Individual TLUL signal values are
  // packed by clearing existing value bits and setting new value bits.
  if (start_word_ind == end_word_ind) {
    // clear existing signal value
    dut_.tl_i[start_word_ind] &= ~(((1U << width) - 1) << start_bit_ind);
    // set new signal value
    dut_.tl_i[start_word_ind] |= value << start_bit_ind;
  } else if ((end_word_ind - 1) == start_word_ind) {
    // Operate on LOWER word
    // Compute width of the low portion of the signal
    uint8_t low_width = OT_TL_O_WORD_SIZE_BITS - start_bit_ind;
    // Clear existing signal value
    dut_.tl_i[start_word_ind] &= ~(((1U << low_width) - 1) << start_bit_ind);
    // TODO(ttrippel): zero out upper bits of value that are shifted past width?
    dut_.tl_i[start_word_ind] |= value << start_bit_ind;

    // Operate on UPPER word
    uint32_t high_mask = (1U << (end_bit_ind + 1)) - 1;
    // Clear existing signal value
    dut_.tl_i[end_word_ind] &= ~((1U << (end_bit_ind + 1)) - 1);
    // TODO(ttrippel): zero out lower bits of value that are shifted past width?
    dut_.tl_i[end_word_ind] |= value >> low_width;
  } else {
    // TODO(ttrippel): RAISE ERROR
  }
}

// Unpacks the given TL-UL signal name from the pointer to the provided array
// TODO(ttrippel): Verify that the given signal name is contained in the packed
// signal byte array.
uint32_t TLULHostTb::UnpackSignal(uint32_t* packed_signals,
                                  std::string signal_name) {
  // Compute start/end word and bit indices of target value
  uint32_t index = signal2index_.at(signal_name);
  uint32_t width = signal2width_.at(signal_name);
  uint8_t start_word_ind = index / OT_TL_O_WORD_SIZE_BITS;
  uint8_t end_word_ind = (index + width - 1) / OT_TL_O_WORD_SIZE_BITS;
  uint8_t start_bit_ind = index - (start_word_ind * OT_TL_O_WORD_SIZE_BITS);
  uint8_t end_bit_ind =
      index + width - 1 - (end_word_ind * OT_TL_O_WORD_SIZE_BITS);
  uint32_t signal = 0;

  // If word indices are the same, signal bits resides in the same word,
  // otherwise, the bits straddle two words. Numeric values of individual TLUL
  // signals are unpacked by shifting and masking.
  if (start_word_ind == end_word_ind) {
    signal = packed_signals[start_word_ind] >> start_bit_ind;
    signal &= (1U << width) - 1;
  } else if ((end_word_ind - 1) == start_word_ind) {
    // Compute width of the low portion of the signal
    uint8_t low_width = OT_TL_O_WORD_SIZE_BITS - start_bit_ind;

    // Shift THEN mask LOW subword
    uint32_t signal_low = packed_signals[start_word_ind] >> start_bit_ind;
    signal_low &= (1U << low_width) - 1;

    //  Mask THEN shift HIGH subword
    uint32_t high_mask = (1U << (end_bit_ind + 1)) - 1;
    uint32_t signal_high = (packed_signals[end_word_ind] & high_mask)
                           << low_width;
    signal = signal_low | signal_high;
  }
  // TODO(ttrippel): RAISE ERROR
  // else {
  // continue;
  //}

  return signal;
}

// Waits for the device to be ready to receive a host transaction request.
bool TLULHostTb::WaitForDeviceReady() {
  while (!UnpackSignal(dut_.tl_o, "A_READY")) {
    if (ToggleClock(&dut_.clk_i, ONE_CLK_CYCLE)) {
      return true;
    }
  }
#ifdef DEBUG
  std::cout << "Device is ready!" << std::endl;
  PrintD2HSignals();
#endif
  return false;
}

// Waits until the device transaction response is valid.
bool TLULHostTb::WaitForDeviceResponse() {
  while (!UnpackSignal(dut_.tl_o, "D_VALID")) {
    if (ToggleClock(&dut_.clk_i, ONE_CLK_CYCLE)) {
      return true;
    }
  }
#ifdef DEBUG
  std::cout << "Device response is valid!" << std::endl;
  PrintD2HSignals();
#endif
  return false;
}
