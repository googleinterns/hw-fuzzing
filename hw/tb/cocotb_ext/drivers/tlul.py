# TODO(ttrippel): add license

import math
from collections import OrderedDict
from enum import IntEnum

import cocotb
from cocotb.binary import BinaryValue
from cocotb.drivers import BusDriver
from cocotb.triggers import ReadOnly, RisingEdge
from cocotb_ext.packed_signal import PackedSignal

# TODO(ttrippel): make widths auto-configurable, maybe by parsing SV package?
# OpenTitan TL-UL Bus Parameters:
TL_AW = 32  # width of address bus in bits
TL_DW = 32  # width of data bus in bits
TL_AIW = 8  # width of address (host) source ID in bits
TL_DIW = 1  # width of (device) sink ID in bits
TL_DUW = 16  # width of device user bits (TL-UL extension)
TL_DBW = TL_DW >> 3  # number of data bytes in transaction (mask size in # bits)
TL_SZW = math.ceil(math.log2(TL_DBW))  # setting for size A_SIZE/D_SIZE

# TODO(ttrippel): support burt transactions (OpenTitan does not support burst
# transactions so they've been left out for this implementation.


class TLULProtocolError(Exception):
  pass


class _OpcodeA(IntEnum):
  PutFullData = 0
  PutPartialData = 1
  Get = 4


class _OpcodeD(IntEnum):
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

  # TODO(ttrippel): Is a_user configurable? In OpenTitan source code it is set
  # to the size of a struct defining its size (tlul_pkg.sv).
  _tl_i_dependencies = OrderedDict([("a_valid", 1), ("a_opcode", 3),
                                    ("a_param", 3), ("a_size", TL_SZW),
                                    ("a_source", TL_AIW), ("a_address", TL_AW),
                                    ("a_mask", TL_DBW), ("a_data", TL_DW),
                                    ("a_user", 16), ("d_ready", 1)])

  _tl_o_dependencies = OrderedDict([("d_valid", 1), ("d_opcode", 3),
                                    ("d_param", 3), ("d_size", TL_SZW),
                                    ("d_source", TL_AIW), ("d_sink", TL_DIW),
                                    ("d_data", TL_DW), ("d_user", TL_DUW),
                                    ("d_error", 1), ("a_ready", 1)])

  def __init__(self, entity, name, clock, **kwargs):
    # Initialize bus signals
    BusDriver.__init__(self, entity, name, clock, **kwargs)

    # Set TL-UL Host-to-Device signal widths
    self._tl_i = PackedSignal(self.bus.tl_i, self._tl_i_dependencies, self.log)

    # Set TL-UL Device-to-Host signal widths
    self._tl_o = PackedSignal(self.bus.tl_o, self._tl_o_dependencies, self.log)

    # Drive some sensible default outputs (setimmediatevalue to avoid x asserts)
    self.bus.tl_i.setimmediatevalue(self._tl_i.pack())

    # TODO(ttrippel): add mutexes for each channel we host to prevent contention
    # when we have multiple TLULHosts driving the bus.

    # log initial state of TL-UL signals
    self.log.debug("TL-UL bus signals initialized to:")
    self.log.debug(self._tl_i.signal2str())
    self.log.debug(self._tl_o.signal2str())

  async def _wait_for_device_ready(self):
    """Wait until Device is ready to receive the transmission (A_READY high)."""
    while True:
      await ReadOnly()
      if self._tl_o.unpack("a_ready"):
        return
      await RisingEdge(self.clock)

  async def _clear_request_after_delay(self, delay=1):
    """Clear request after <delay> clock cycles from A_READY going high."""
    for _ in range(delay):
      await RisingEdge(self.clock)
    self.bus.tl_i <= self._tl_i.pack(d_ready=1)

  async def _wait_for_device_response(self):
    """Wait to until Device has responded (D_VALID high)."""
    while True:
      await ReadOnly()
      if self._tl_o.unpack("d_valid"):
        self.log.debug(self._tl_o.signal2str())
        return
      await RisingEdge(self.clock)

  async def _send_tlul_request(self,
                               opcode: int,
                               address: int,
                               data: int,
                               size: int,
                               mask: int,
                               sync: bool = True):
    """Sends put/get (write/read) request."""
    # Synchronize request with next rising clock edge
    if sync:
      await RisingEdge(self.clock)

    # Put WRITE request on the bus
    self.bus.tl_i <= self._tl_i.pack(a_valid=1,
                                     a_opcode=opcode,
                                     a_size=size,
                                     a_address=address,
                                     a_data=data,
                                     a_mask=mask,
                                     d_ready=1)
    self.log.debug(self._tl_i.signal2str())

    # Wait for request to be recieved by device
    await self._wait_for_device_ready()
    await self._clear_request_after_delay()

  async def _receive_tlul_put_response(self):
    """Receive Device response form a put (write) request."""
    # Wait to until Device has responded (D_VALID high)
    await self._wait_for_device_response()
    d_opcode = self._tl_o.unpack("d_opcode")
    d_error = self._tl_o.unpack("d_error")

    # raise TLULException if error occurs
    if d_error.integer or d_opcode != _OpcodeD.AccessAck:
      self.log.error(self._tl_o.signal2str())
      raise TLULProtocolError("Put failed.")

  @cocotb.coroutine
  async def put_partial(self,
                        address: int,
                        data: int,
                        size: int,
                        mask: int,
                        sync: bool = True):
    """Write a value (less than the size of the full data bus) to an address.

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
      TLULProtocolError: If invalid address, size, or mask inputs, or write
      response from TLUL asserts d_error or invalid opcode.
    """

    # Validate size
    if size > TL_SZW:
      raise TLULProtocolError(f"Get: size must be <= {size}.")
      return

    # TODO(ttrippel): Validate address and mask match given size of transaction
    # lower_addr_nibble = address & ((1 << TL_SZW) - 1)

    # Send request and wait for response
    await self._send_tlul_request(_OpcodeA.PutPartialData, address, data, size,
                                  mask, sync)
    await self._receive_tlul_put_response()

  @cocotb.coroutine
  async def put_full(self, address: int, data: int, sync: bool = True):
    """Write a value to an address.

    Args:
      address: The address to write to.
      data: The data to write to the address.
      sync: Wait for rising edge on clock initially.
        Defaults to True

    Returns:
      The write response value.

    Raises:
      TLULProtocolError: If write response asserts d_error or invalid opcode.
    """
    # TODO: add size and mask as input parameters and validate them.
    # Note: technically, the TL-UL spec. allows for full data writes for
    # registers smaller than the bus width, but OpenTitan documentation states
    # PutFullData operations should set a_size to full data bus width. This may
    # be because all IP registers are at word aligned addresses?

    # Send request and wait for response
    await self._send_tlul_request(_OpcodeA.PutFullData, address, data, TL_SZW,
                                  2**TL_DBW - 1, sync)
    await self._receive_tlul_put_response()

  @cocotb.coroutine
  async def get(self, address: int, sync: bool = True) -> BinaryValue:
    """Read from an address.

    Args:
      address: The address to read from.
      sync: Wait for rising edge on clock initially.
        Defaults to True

    Returns:
      The read data value.

    Raises:
      TLULProtocolError: If write response asserts d_error or invalid opcode.
    """
    # TODO: add size and mask as input parameters and validate them.
    # Note: technically, the TL-UL spec. allows for reads from addresses that
    # are NOT naturally aligned, and/or smaller than the data-bus width,
    # provided the size and mask values are set appropriately. However,
    # OpenTitan TL-UL documentation states Get operations "read [the] full bus
    # width", i.e. a_size and a_mask should be set to data bus width. This may
    # be because all IP registers are at word aligned addresses?

    # Send request and wait for response
    await self._send_tlul_request(_OpcodeA.Get, address, 0, TL_SZW,
                                  (2**TL_DBW) - 1, sync)
    await self._wait_for_device_response()

    # Unpack response and data
    d_data = self._tl_o.unpack("d_data")
    d_opcode = self._tl_o.unpack("d_opcode")
    d_error = self._tl_o.unpack("d_error")

    # raise TLULException if error occurs
    if d_error.integer or d_opcode != _OpcodeD.AccessAckData:
      self.log.error(self._tl_o.signal2str())
      raise TLULProtocolError("Get failed.")

    return d_data
