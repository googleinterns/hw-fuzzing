# TODO(ttrippel): add license

from collections import OrderedDict
from enum import IntEnum

import cocotb
from cocotb.binary import BinaryValue
from cocotb.drivers import BusDriver
from cocotb.triggers import ReadOnly, RisingEdge
from cocotb_ext.packed_signal import PackedSignal


class TLULProtocolError(Exception):
  pass


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

  # OpenTitan TL-UL Bus Parameters:
  # TL_UL Defines from OpenTitan top_pkg:
  # TL_AW = 32  # width of address bus in bits
  # TL_DW = 32  # width of data bus in bits
  # TL_AIW = 8  # width of address (host) source ID in bits
  # TL_DIW = 1  # width of (device) sink ID in bits
  # TL_DUW = 4  # width of device user bits (TL-UL extension)
  # TL_DBW = TL_DW >> 3  # number of data bytes in transaction
  # TL_SZW = math.ceil(math.log2(TL_DBW))  # setting for size A_SIZE/D_SIZE

  # TODO(ttrippel): make widths configurable, maybe by parsing SV package?
  _tl_i_dependencies = OrderedDict([("a_valid", 1), ("a_opcode", 3),
                                    ("a_param", 3), ("a_size", 2),
                                    ("a_source", 8), ("a_address", 32),
                                    ("a_mask", 4), ("a_data", 32),
                                    ("a_user", 16), ("d_ready", 1)])

  # TODO(ttrippel): make widths configurable, maybe by parsing SV package?
  _tl_o_dependencies = OrderedDict([("d_valid", 1), ("d_opcode", 3),
                                    ("d_param", 3), ("d_size", 2),
                                    ("d_source", 8), ("d_sink", 1),
                                    ("d_data", 32), ("d_user", 16),
                                    ("d_error", 1), ("a_ready", 1)])

  def __init__(self, entity, name, clock, **kwargs):
    # Initialize bus signals
    BusDriver.__init__(self, entity, name, clock, **kwargs)

    # Set TL-UL Host-to-Device signal widths
    self._tl_i = PackedSignal(self.bus.tl_i, self._tl_i_dependencies, self.log)

    # Set TL-UL Device-to-Host signal widths
    self._tl_o = PackedSignal(self.bus.tl_o, self._tl_o_dependencies, self.log)

    # Drive some sensible default outputs (setimmediatevalue to avoid x asserts)
    # self.bus.tl_i.setimmediatevalue(
    # self._tl_i.pack(a_address=int("DEADBEEF", 16)))
    self.bus.tl_i.setimmediatevalue(self._tl_i.pack())

    # TODO(ttrippel): add mutexes for each channel we host to prevent contention

    # log initial state of TL-UL signals
    self.log.debug("TL-UL bus signals initialized to:")
    self.log.debug(self._tl_i.signal2str())
    self.log.debug(self._tl_o.signal2str())

  @cocotb.coroutine
  async def put_full(self,
                     address: int,
                     data: int,
                     size: int,
                     mask: int,
                     sync: bool = True) -> BinaryValue:
    """Write a value to an address.

    Args:
      address: The address to write to.
      data: The data to write to the address.
      size: The number of data bytes to write (2^size == number of bytes).
      mask: The bytes of the data field to write. (Each bit is a byte mask.)
      sync: Wait for rising edge on clock initially.
        Defaults to True

    Returns:
      The write response value.

    Raises:
      TLULProtocolError: If read response from TLUL asserts d_error or
      unexpected response opcode is observed.
    """
    if sync:
      await RisingEdge(self.clock)

    # Put read request on the bus
    self.bus.tl_i <= self._tl_i.pack(a_valid=1,
                                     a_opcode=TL_A_Opcode.PutFullData,
                                     a_size=size,
                                     a_address=address,
                                     a_data=data,
                                     a_mask=mask,
                                     d_ready=1)

    # Wait until the Device is ready to receive the transmission (A_READY high)
    while True:
      await ReadOnly()
      if self._tl_o.unpack("a_ready"):
        break
      await RisingEdge(self.clock)

    # Clear request after one clock cycle from A_READY going high
    await RisingEdge(self.clock)
    self.bus.tl_i <= self._tl_i.pack(d_ready=1)

    # Wait to until Device has responded (D_VALID high)
    while True:
      await ReadOnly()
      if self._tl_o.unpack("d_valid"):
        self.log.debug(self._tl_o.signal2str())
        d_opcode = self._tl_o.unpack("d_opcode")
        d_error = self._tl_o.unpack("d_error")
        break
      await RisingEdge(self.clock)

    # raise TLULException if error occurs
    if d_error.integer or d_opcode != TL_D_Opcode.AccessAck:
      raise TLULProtocolError(
          f"Get {address} failed with response:\n{self._tl_o.signal2str()}")

    return d_opcode

  @cocotb.coroutine
  async def get(self,
                address: int,
                size: int,
                mask: int,
                sync: bool = True) -> BinaryValue:
    """Read from an address.

    Args:
      address: The address to read from.
      size: The number of data bytes to write (2^size == number of bytes).
      mask: The bytes of the data field to write. (Each bit is a byte mask.)
      sync: Wait for rising edge on clock initially.
        Defaults to True

    Returns:
      The read data value.

    Raises:
      TLULProtocolError: If read response from TLUL asserts d_error or
      unexpected response opcode is observed.
    """
    if sync:
      await RisingEdge(self.clock)

    # Put read request on the bus
    self.bus.tl_i <= self._tl_i.pack(a_valid=1,
                                     a_opcode=TL_A_Opcode.Get,
                                     a_size=size,
                                     a_address=address,
                                     a_mask=mask,
                                     d_ready=1)

    # Wait until the Device is ready to receive the transmission (A_READY high)
    while True:
      await ReadOnly()
      if self._tl_o.unpack("a_ready"):
        break
      await RisingEdge(self.clock)

    # Clear request after one clock cycle from A_READY going high
    await RisingEdge(self.clock)
    self.bus.tl_i <= self._tl_i.pack(d_ready=1)

    # Wait to until Device data is ready to read data (D_VALID high)
    while True:
      await ReadOnly()
      if self._tl_o.unpack("d_valid"):
        self.log.debug(self._tl_o.signal2str())
        d_data = self._tl_o.unpack("d_data")
        d_opcode = self._tl_o.unpack("d_opcode")
        d_error = self._tl_o.unpack("d_error")
        break
      await RisingEdge(self.clock)

    # raise TLULException if error occurs
    if d_error.integer or d_opcode != TL_D_Opcode.AccessAckData:
      raise TLULProtocolError(
          f"Get {address} failed with response:\n{self._tl_o.signal2str()}")

    return d_data
