# TODO(ttrippel): add license

import struct
from enum import IntEnum

import cocotb
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

  # _signals = [
  # "A_VALID", "A_READY", "A_OPCODE", "A_PARAM", "A_ADDRESS", "A_DATA",
  # "A_SOURCE", "A_SIZE", "A_MASK", "D_VALID", "D_READY", "D_OPCODE",
  # "D_ERROR", "D_PARAM", "D_SIZE", "D_DATA", "D_SOURCE", "D_SINK"
  # ]

  # _optional_signals = ["A_USER", "D_USER"]

  _signals = ["tl_i", "tl_o"]

  def __init__(self, entity, name, clock, **kwargs):
    BusDriver.__init__(self, entity, name, clock, **kwargs)

    # tl_i (TL-UL input to DEVICE, output from HOST (this driver))
    print()
    print("TLUL DEVICE INPUT:")
    print(type(self.bus.tl_i))
    print(type(self.bus.tl_i.value))
    print(dir(self.bus.tl_i))
    print(self.bus.tl_i.value.binstr)
    print(len(self.bus.tl_i.value))
    print(self.bus.tl_i.get_definition_name())

    # tl_o (TL-UL output from DEVICE, input to HOST (this driver))
    print()
    print("TLUL DEVICE OUTPUT:")
    print(type(self.bus.tl_o))
    print(type(self.bus.tl_o.value))
    print(dir(self.bus.tl_o))
    print(self.bus.tl_o.value.binstr)
    print(len(self.bus.tl_o.value))
    print(self.bus.tl_o.get_definition_name())

    # Drive some sensible default outputs (setimmediatevalue to avoid x asserts)
    a_valid = int("1", 2)
    a_opcode = int(TL_A_Opcode.PutFullData)
    a_param = int("111", 2)
    a_size = 0
    a_source = int("11111111", 2)
    a_address = 0
    a_mask = 15
    a_data = 0
    a_user = 0
    d_ready = 0
    tl_i = self.pack_tl_h2d(a_valid, a_opcode, a_param, a_size, a_source,
                            a_address, a_mask, a_data, a_user, d_ready)
    self.bus.tl_i.setimmediatevalue(BinaryValue(tl_i))
    tl_i = self.bus.tl_i.value.binstr
    print()
    print(tl_i)
    assert int(tl_i[0], 2) == a_valid
    assert int(tl_i[1:4], 2) == a_opcode
    assert int(tl_i[4:7], 2) == a_param
    assert int(tl_i[7:9], 2) == a_size

    # Mutex for each channel that we host to prevent contention
    # self.write_address_busy = Lock("%s_wabusy" % name)
    # self.read_address_busy = Lock("%s_rabusy" % name)
    # self.write_data_busy = Lock("%s_wbusy" % name)

  def pack_tl_h2d(self, a_valid: int, a_opcode: int, a_param: int, a_size: int,
                  a_source: int, a_address: int, a_mask: int, a_data: int,
                  a_user: int, d_ready: int) -> bytes:
    """Creates a packed struct for input to a TL-UL device."""

    # Create a packed struct of 104 bits
    # OpenTitan IP input accepts a TileLink input of 102 bits wide)
    # "=" = standard size and native endianness
    # B = unsigned char (1 byte); Q = unsigned long long (8 bytes)
    tl_h2d = struct.Struct(">4I")

    # form word 0 -- contains first 6 bits of tl_h2d_t SV struct
    tl_h2d_w0 = 0
    tl_h2d_w0 = a_valid
    tl_h2d_w0 <<= 3
    tl_h2d_w0 |= a_opcode
    tl_h2d_w0 <<= 2
    tl_h2d_w0 |= (a_param >> 1)

    # form word 1 -- contains next 32 bits of tl_h2d_t SV struct
    tl_h2d_w1 = 0
    tl_h2d_w1 |= (a_param & 1)  # grab LSB
    tl_h2d_w1 <<= 2  # TL_SZW in OT top_pkg
    tl_h2d_w1 |= a_size
    tl_h2d_w1 <<= 8  # TL_AIW in OT top_pkg
    tl_h2d_w1 |= a_source
    tl_h2d_w1 <<= 21  # part of TL_AW in OT top_pkg
    tl_h2d_w1 |= (a_address >> 11)

    # form word 2 -- contains next 32 bits of tl_h2d_t SV struct
    tl_h2d_w2 = 0
    tl_h2d_w2 |= (a_address & 2047)  # grab remaining first 11 LSBs
    tl_h2d_w2 <<= 4  # TL_DBW in OT top_pkg
    tl_h2d_w2 |= a_mask
    tl_h2d_w2 <<= 17  # part of TL_DW in OT top_pkg
    tl_h2d_w2 |= (a_data >> 15)

    # form word 3 -- contains next 32 bits of tl_h2d_t SV struct
    tl_h2d_w3 = 0
    tl_h2d_w3 |= (a_data & 32767)  # grab remaining 15 first LSBs
    tl_h2d_w3 <<= 16  # TL_AUW in OT top_pkg
    tl_h2d_w3 |= a_user
    tl_h2d_w3 <<= 1
    tl_h2d_w3 |= d_ready

    return tl_h2d.pack(tl_h2d_w0, tl_h2d_w1, tl_h2d_w2, tl_h2d_w3)

  @cocotb.coroutine
  async def get(self, address: int, sync: bool = True) -> BinaryValue:
    """Read from an address.

    Args:
      address: The address to read from.

    Returns:
      The read data value.

    Raises:
      TLULException: ...
    """
    return
