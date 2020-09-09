# TODO(ttrippel): add license

import math

import cocotb
from cocotb.binary import BinaryValue
from cocotb.drivers import BusDriver
from cocotb.triggers import Event, ReadOnly, RisingEdge


class TLULException(Exception):
  pass


# Questions:
# 1. is D_DATA only associated with a READ? like A_DATA is only associated with
# a write?

# TL_AW = 32  # width of address bus in bits
# TL_DW = 32  # width of data bus in bits
# TL_AIW = 8  # width of address (host) source ID in bits
# TL_DIW = 1  # width of (device) sink ID in bits
# TL_DUW = 4  # width of device user bits (TL-UL extension)
# TL_DBW = TL_DW >> 3  # number of data bytes in transaction
# TL_SZW = math.ceil(math.log2(TL_DBW))  # setting for size A_SIZE/D_SIZE


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

  _signals = [
      "A_VALID", "A_READY", "A_OPCODE", "A_PARAM", "A_ADDRESS", "A_DATA",
      "A_SOURCE", "A_SIZE", "A_MASK", "D_VALID", "D_READY", "D_OPCODE",
      "D_ERROR", "D_PARAM", "D_SIZE", "D_DATA", "D_SOURCE", "D_SINK"
  ]

  _optional_signals = ["A_USER", "D_USER"]

  def __init__(self, entity, name, clock, **kwargs):
    BusDriver.__init__(self, entity, name, clock, **kwargs)
    self._a_source = kwargs["host_id"]
    self._a_size = math.ceil(math.log2(kwargs["data_size_bytes"]))

    # Drive some sensible default outputs (setimmediatevalue to avoid x asserts)
    self.bus.A_VALID.setimmediatevalue(0)
    self.bus.A_OPCODE.setimmediatevalue(0)
    self.bus.A_PARAM.setimmediatevalue(0)
    self.bus.A_ADDRESS.setimmediatevalue(0)
    self.bus.A_DATA.setimmediatevalue(0)
    self.bus.A_SOURCE.setimmediatevalue(0)
    self.bus.A_SIZE.setimmediatevalue(2)
    self.bus.A_MASK.setimmediatevalue(0)
    self.bus.A_USER.setimmediatevalue(0)
    self.bus.D_READY.setimmediatevalue(0)

    # Mutex for each channel that we host to prevent contention
    # self.write_address_busy = Lock("%s_wabusy" % name)
    # self.read_address_busy = Lock("%s_rabusy" % name)
    # self.write_data_busy = Lock("%s_wbusy" % name)

  @cocotb.coroutine
  async def get(self, address: int) -> BinaryValue:
    """Read from an address.

    Args:
      address: The address to read from.

    Returns:
      The read data value.

    Raises:
      TLULException: ...
    """
    return
