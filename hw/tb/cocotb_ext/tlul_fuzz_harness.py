# TODO(ttrippel): add license
"""Cocotb testbench harness to interface a TL-UL driven IP core with AFL.

Description:
The testbench instantiates a TileLink Uncached Lightweight (TL-UL) driver to
interface with a DUT with a matching bus interface. It starts by reseting the
DUT for a duration of DUT_RESET_DURATION_NS nanoseconds. After reset, the
testbench reads opcode and address/data bytes from STDIN and feeds them to
the TL-UL driver to exercise the DUT. The testbench proceeds until there are no
more opcodes to read. Hardware fuzzing opcodes are described below. Also
provided is an example byte sequence for each hardware fuzzing opcode.

HW Fuzzing Opcodes (encoded with 1-byte):
  1. WAIT  -- one clock cycle
  2. READ  -- TL-UL Get -- followed by a sequence of address bytes
  3. WRITE -- TL-UL Put -- followed by a sequence of address AND data bytes

Since there exists only three HW fuzzing opcodes, and they are encoded with a
single byte, we map each of these opcodes to equal-sized ranges of values within
the range of 0 to 255 (inclusive) to give enable the fuzzer and equally-likely
chance at generating all opcodes when the fuzzing begins. The thresholds are
defined here as:
 1. WAIT  == [0, 85)
 2. READ  == [85, 170)
 3. WRITE == [170, 255]

Example AFL Seed File Format:
--------------------------------------------------------------------------------
|wait|read|address|read|address|write|address|data|write|address|data|wait|wait|
--------------------------------------------------------------------------------
|read|address|read|address|...
---------------------------

Opcode and Address/Data Sizes:
  1. Opcode: 1-byte
  2. Address: configurable via env. var. ADDRESS_SIZE (4-bytes for OpenTitan IP)
  3. Data: configurable via env. var. DATA_SIZE (4-bytes for OpenTitan IP)

Note on Environment Vars:
Since cocotb does not support passing arguments to the tests implemented in
Python, any arguments must be passed as environment variables. The environment
variables that must be defined to run a test in this testbench are described for
each test function.
"""

import logging
import math
import os
import sys
from enum import IntEnum

import cocotb
from cocotb.binary import BinaryValue
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Import custom cocotb extension packages
sys.path.append("/Users/ttrippel/repos/hw-fuzzing/hw/tb")
from cocotb_ext.drivers.tlul import TLULHost

ENDIANNESS = "big"  # how to interpret bytes from STDIN
OPCODE_SIZE = 1  # number of opcode bytes to read from STDIN
WAIT_OPCODE_THRESHOLD = 85
RW_OPCODE_THRESHOLD = 170


class HWFuzzOpcode(IntEnum):
  """Hardware fuzzer opcode derived from AFL generated inputs."""
  wait = 1
  read = 2
  write = 3


def bin2hex(value: BinaryValue) -> str:
  """Converts cocotb BinaryValue to a hex string."""
  hex_width = math.ceil(len(value.binstr) / 4.0)
  return f"0x{value.integer:0>{hex_width}X}"


class TLULFuzzHarness():
  """A class to fuzz HW cores with TL-UL bus interfaces.

  Attributes:
    dut: Design under test.
    tlul: TL-UL bus driver (Host).
    clock: Cocotb clock object.

  Note:
    The following ennvironment variables are required to be set:
      ADDRESS_SIZE: Size of TL-UL address bus (# bytes).
      DATA_SIZE: Size of TL-UL data bus (# bytes).
  """
  def __init__(self, dut, clk_period_ns, debug=False):
    """Instantiates TL-UL driver/clock and configures interface loggers."""
    self.dut = dut
    self.tlul = TLULHost(dut, "", dut.clk_i)
    self.clock = Clock(dut.clk_i, clk_period_ns, units="ns")

    # Set verbosity on DUT and TL-UL driver
    logging_level = logging.DEBUG if debug else logging.INFO
    self.tlul.log.setLevel(logging_level)
    self.dut._log.setLevel(logging_level)

    # Read TL-UL bus arameters defined as environment variables
    self.address_size = int(os.getenv("ADDRESS_SIZE"))
    self.data_size = int(os.getenv("DATA_SIZE"))
    self.dut._log.info(f"Address Size (bytes): {self.address_size}")
    self.dut._log.info(f"Data Size (bytes):    {self.data_size}")

    # start the clock
    cocotb.fork(self.clock.start())

  def get_fuzzer_opcode(self):
    """Reads a single byte from STDIN and maps it to one of three opcodes."""
    # create ~equal oportunity for each opcode type
    fuzzer_opcode_bytes = sys.stdin.buffer.read(OPCODE_SIZE)
    if len(fuzzer_opcode_bytes) == OPCODE_SIZE:
      fuzzer_opcode = int.from_bytes(fuzzer_opcode_bytes,
                                     byteorder=ENDIANNESS,
                                     signed=False)
      if fuzzer_opcode < WAIT_OPCODE_THRESHOLD:
        # hw_fuzz_opcode_str = "wait"
        hw_fuzz_opcode = HWFuzzOpcode.wait
      elif fuzzer_opcode < RW_OPCODE_THRESHOLD:
        # hw_fuzz_opcode_str = "read"
        hw_fuzz_opcode = HWFuzzOpcode.write
      else:
        # hw_fuzz_opcode_str = "write"
        hw_fuzz_opcode = HWFuzzOpcode.read
      return hw_fuzz_opcode
    else:
      return None

  def get_tlul_address(self):
    """Reads ADDRESS_SIZE bytes from STDIN as the address for a transaction."""
    address_bytes = sys.stdin.buffer.read(self.address_size)
    if len(address_bytes) == self.address_size:
      return int.from_bytes(address_bytes, byteorder=ENDIANNESS, signed=False)
    else:
      return None

  def get_tlul_data(self):
    """Reads DATA_SIZE bytes from STDIN as the data for a transaction."""
    data_bytes = sys.stdin.buffer.read(self.data_size)
    if len(data_bytes) == self.data_size:
      return int.from_bytes(data_bytes, byteorder=ENDIANNESS, signed=False)
    else:
      return None

  async def reset(self, duration_ns):
    """Resets the DUT."""
    self.dut._log.debug("Resetting the DUT ...")
    self.dut.rst_ni <= 0
    self.tlul.bus.tl_i <= 0
    await Timer(duration_ns, units="ns")
    await RisingEdge(self.dut.clk_i)
    self.dut.rst_ni <= 1
    self.dut._log.debug("Reset complete!")
