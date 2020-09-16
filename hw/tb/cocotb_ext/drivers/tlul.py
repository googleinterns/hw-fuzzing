# TODO(ttrippel): add license

import math
import struct
from collections import OrderedDict
from enum import IntEnum

import cocotb
import prettytable
from cocotb.binary import BinaryValue
from cocotb.drivers import BusDriver
from cocotb.triggers import Event, ReadOnly, RisingEdge


class TLULException(Exception):
  pass


# Questions:
# 1. is D_DATA only associated with a READ? like A_DATA is only associated with
# a write?

# TL_UL Defines from OpenTitan top_pkg:
# TL_AW = 32  # width of address bus in bits
# TL_DW = 32  # width of data bus in bits
# TL_AIW = 8  # width of address (host) source ID in bits
# TL_DIW = 1  # width of (device) sink ID in bits
# TL_DUW = 4  # width of device user bits (TL-UL extension)
# TL_DBW = TL_DW >> 3  # number of data bytes in transaction
# TL_SZW = math.ceil(math.log2(TL_DBW))  # setting for size A_SIZE/D_SIZE


class TL_A_Opcode(IntEnum):
  PutFullData = 0
  PutPartialData = 1
  Get = 4


class TL_D_Opcode(IntEnum):
  AccessAck = 0
  AccessAckData = 1


class TLULHost(BusDriver):
  """TL-UL Host.

  Signals:
    Channel A (Host REQUEST to a Device):
      A_VALID:   (output) request from host is valid
      A_READY:   (input)  device accepts request from host
      A_OPCODE:  (output) request opcode (read, write, or partial write)
      A_PARAM:   (output) unused
      A_ADDRESS: (output) request address of configurable width
      A_DATA:    (output) write request data of configurable width
      A_SOURCE:  (output) request host ID of configurable width
      A_SIZE:    (output) request size (2^A_SIZE; e.g., 0=1-byte, 1=2-bytes...)
      A_MASK:    (output) write stobe, one bit/byte indicating valid data lanes
      A_USER:    (output) extension to TL-UL spec. for OpenTitan IP cores

    Channel D (Device RESPONSE to Host REQUEST):
      D_VALID:   (input)  response from device is valid
      D_READY:   (output) host accepts response from device
      D_OPCODE:  (input)  response opcode (ack or data)
      D_ERROR:   (input)  response is an error
      D_PARAM:   (input)  unused
      D_SIZE:    (input)  response size (format same as A_SIZE)
      D_DATA:    (input)  response data of configurable width
      D_SOURCE:  (input)  bouncing of request host ID (A_SOURCE)
      D_SINK:    (input)  response device ID of a configurable width
      D_USER:    (input)  extension to TL-UL spec. for OpenTitan IP cores
  """
  _signals = ["tl_i", "tl_o"]

  def __init__(self, entity, name, clock, **kwargs):
    # Initialize bus signals
    BusDriver.__init__(self, entity, name, clock, **kwargs)

    # Set TL-UL Host-to-Device signal widths
    # TODO(ttrippel): make these configurable and remove assertions
    self._h2d_widths = OrderedDict([("a_valid", (1, 0)), ("a_opcode", (3, 1)),
                                    ("a_param", (3, 4)), ("a_size", (2, 7)),
                                    ("a_source", (8, 9)),
                                    ("a_address", (32, 17)),
                                    ("a_mask", (4, 49)), ("a_data", (32, 53)),
                                    ("a_user", (16, 85)),
                                    ("d_ready", (1, 101))])
    self._h2d_width = sum(w for s, (w, o) in self._h2d_widths.items())
    assert self._h2d_width == len(self.bus.tl_i.value.binstr), \
        "Host-to-Device signal width settings are incorrect."

    # Set TL-UL Device-to-Host signal widths
    # TODO(ttrippel): make these configurable and remove assertions
    self._d2h_widths = OrderedDict([("d_valid", (1, 0)), ("d_opcode", (3, 1)),
                                    ("d_param", (3, 4)), ("d_size", (2, 7)),
                                    ("d_source", (8, 9)), ("d_sink", (1, 17)),
                                    ("d_data", (32, 18)), ("d_user", (16, 50)),
                                    ("d_error", (1, 66)),
                                    ("a_ready", (1, 67))])
    self._d2h_width = sum(w for s, (w, o) in self._d2h_widths.items())
    assert self._d2h_width == len(self.bus.tl_o.value.binstr), \
        "Device-to-Host signal width settings are incorrect."

    # Drive some sensible default outputs (setimmediatevalue to avoid x asserts)
    # tl_i = self._pack_h2d_signals(a_address=int("deadbeef", 16))
    tl_i = self._pack_h2d_signals()
    self.bus.tl_i.setimmediatevalue(tl_i)

    # Mutex for each channel that we host to prevent contention
    # self.write_address_busy = Lock("%s_wabusy" % name)
    # self.read_address_busy = Lock("%s_rabusy" % name)
    # self.write_data_busy = Lock("%s_wbusy" % name)

    # print initial state of TL-UL signals
    self.log.info("TL-UL bus signals initialized to:")
    self._print_tl_signals("h2d")
    self._print_tl_signals("d2h")
    print()

  def _unpack_d2h_signals(self, signal: str) -> int:
    """Unpacks Device-to-Host signals."""
    (width, offset) = self._d2h_widths[signal]
    return int(self.bus.tl_o.value.binstr[offset:offset + width], 2)

  def _pack_h2d_signals(self,
                        a_valid: int = 0,
                        a_opcode: int = 0,
                        a_param: int = 0,
                        a_size: int = 0,
                        a_source: int = 0,
                        a_address: int = 0,
                        a_mask: int = 0,
                        a_data: int = 0,
                        a_user: int = 0,
                        d_ready: int = 0) -> BinaryValue:
    """Creates a packed struct for input to a TL-UL device."""

    # packed_h2d_signals = BinaryValue(0, n_bits=self._h2d_width)
    # idx = 0
    # for signal, width in self._h2d_widths.items():
    # # packed_h2d_signals.value = packed_h2d_signals.value.integer << width
    # packed_h2d_signals.value = (packed_h2d_signals.integer >> width) | (
    # vars()[signal] & (2**width - 1))
    # print(
    # f"Signal: {signal}; Width: {width}; Value: {(vars()[signal] & (2**width - 1)):b}"
    # )
    # print(packed_h2d_signals.binstr)
    # print()
    # idx += width
    # return packed_h2d_signals

    # Create a packed struct of 10 bits
    # OpenTitan IP input accepts a TileLink input of 102 bits wide)
    # "=" = standard size and native endianness
    # B = unsigned char (1 byte); Q = unsigned long long (8 bytes)
    h2d_signals = struct.Struct(">4I")

    # form word 0 -- contains first 6 bits of tl_h2d_t SV struct
    h2d_w0 = 0
    h2d_w0 = a_valid
    h2d_w0 <<= 3
    h2d_w0 |= a_opcode
    h2d_w0 <<= 2
    h2d_w0 |= (a_param >> 1)

    # form word 1 -- contains next 32 bits of tl_h2d_t SV struct
    h2d_w1 = 0
    h2d_w1 |= (a_param & 1)  # grab LSB
    h2d_w1 <<= 2  # TL_SZW in OT top_pkg
    h2d_w1 |= a_size
    h2d_w1 <<= 8  # TL_AIW in OT top_pkg
    h2d_w1 |= a_source
    h2d_w1 <<= 21  # part of TL_AW in OT top_pkg
    h2d_w1 |= (a_address >> 11)

    # form word 2 -- contains next 32 bits of tl_h2d_t SV struct
    h2d_w2 = 0
    h2d_w2 |= (a_address & 2047)  # grab remaining first 11 LSBs
    h2d_w2 <<= 4  # TL_DBW in OT top_pkg
    h2d_w2 |= a_mask
    h2d_w2 <<= 17  # part of TL_DW in OT top_pkg
    h2d_w2 |= (a_data >> 15)

    # form word 3 -- contains next 32 bits of tl_h2d_t SV struct
    h2d_w3 = 0
    h2d_w3 |= (a_data & 32767)  # grab remaining 15 first LSBs
    h2d_w3 <<= 16  # TL_AUW in OT top_pkg
    h2d_w3 |= a_user
    h2d_w3 <<= 1
    h2d_w3 |= d_ready

    # pack TL-UL Host-to-Device signals
    return BinaryValue(h2d_signals.pack(h2d_w0, h2d_w1, h2d_w2, h2d_w3))

  def _print_tl_signals(self, signals_2_print):
    """Prints current state of TL-UL signals for debugging."""
    # determine which signals to print (Host-to-Device or Device-to-Host)
    if signals_2_print == "h2d":
      packed_signals = self.bus.tl_i
      widths = self._h2d_widths
      title_str = "TL-UL Host-to-Device Signals"
    else:
      packed_signals = self.bus.tl_o
      widths = self._d2h_widths
      title_str = "TL-UL Device-to-Host Signals"

    # create a table and print it
    tl_table = prettytable.PrettyTable(header=True)
    tl_table.field_names = ["Signal", "Width", "Hex Value", "Binary Value"]
    idx = 0
    for signal, (width, _) in widths.items():
      signal_binstr = packed_signals.value.binstr[idx:idx + width]
      signal_int = int(signal_binstr, 2)
      hex_width = math.ceil(width / 4.0)
      tl_table.add_row(
          [signal, width, f"{signal_int:0>{hex_width}X}", signal_binstr])
      idx += width
    tl_table.align = "l"
    tl_table.title = title_str + f" ({idx} bits)"
    self.log.info(tl_table)
    # print(tl_table)

  @cocotb.coroutine
  async def get(self,
                size: int,
                address: int,
                mask: int,
                sync: bool = True) -> BinaryValue:
    """Read from an address.

    Args:
      address: The address to read from.

    Returns:
      The read data value.

    Raises:
      TLULException: ...
    """
    if sync:
      await RisingEdge(self.clock)

    # Put ready request on the bus
    self.bus.tl_i <= self._pack_h2d_signals(a_valid=1,
                                            a_opcode=TL_A_Opcode.Get,
                                            a_size=size,
                                            a_address=address,
                                            a_mask=mask)

    # Wait until the Device is ready to receive the transmission (A_READY high)
    while True:
      await ReadOnly()
      if self._unpack_d2h_signals("a_ready"):
        break
      await RisingEdge(self.clock)

    # Clear Get request after one clock cycle from A_READY going high
    await RisingEdge(self.clock)
    self.bus.tl_i <= self._pack_h2d_signals(a_valid=0)

    # Wait to until Device data is ready to read (D_VALID high)
    while True:
      await ReadOnly()
      # TODO(ttrippel): check if need to signal D_READY high
      if self._unpack_d2h_signals("d_valid"):
        # get the data
        self._print_tl_signals("d2h")
        d_data = self._unpack_d2h_signals("d_data")
        # d_error = self._unpack_d2h_signals("d_error")
        # d_opcode = self._unpack_d2h_signals("d_opcode")
        break
      await RisingEdge(self.clock)

    # check for error(s)
    # check for correct response opcode
    # raise TLULException if any of above occur
    return d_data
