#!/usr/bin/python3
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This is a cocotb testbench harness to interface with afl-fuzz.

Description:
The testbench starts by reseting the DUT for a duration of DUT_RESET_DURATION_NS
nanoseconds. After reset, the testbench reads bytes from STDIN and feeds them to
the input port(s) of the DUT. The testbench proceeds until there are no inputs
more inputs to provide the DUT.

Environment Vars:
Since cocotb does not support passing arguments to the tests implemented in
Python, any arguments must be passed as environment variables.
"""

import os
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb.triggers import Timer

CLK_PERIOD_NS = 10  # duration of simulation clock period
DUT_RESET_DURATION_NS = 50  # duration to hold DUT in reset for in ns


async def reset_dut(reset_n, duration_ns):
  reset_n._log.debug("Resetting DUT ...")
  reset_n <= 0
  await Timer(duration_ns, units="ns")
  reset_n <= 1
  reset_n._log.debug("Reset complete!")


@cocotb.test()
async def lock_tb(dut):
  """Randomly generates input code sequences to try to unlock the lock.

  Args:
    dut: The object representing the DUT being simulated.

  Required Environment Vars:
    NUM_LOCK_STATES: The number of input codes to generate in a sequece.
    LOCK_COMP_WIDTH: The width (in # of bits) of the input code port.

  Returns:
    None
  """

  # Create and start the clock
  clock = Clock(dut.clk, CLK_PERIOD_NS, units="ns")
  cocotb.fork(clock.start())

  # Reset the DUT
  await reset_dut(dut.reset_n, DUT_RESET_DURATION_NS)

  # Get test parameters
  max_length = int(os.getenv("NUM_LOCK_STATES"))
  input_size = 2**int(os.getenv("LOCK_COMP_WIDTH"))

  # Send in random input values
  while True:
    rand_sequence_length = random.randrange(1, max_length)
    for _ in range(rand_sequence_length):
      rand_code = random.randrange(input_size)
      dut._log.info("Setting code to: %d" % rand_code)
      dut.code <= rand_code
      await FallingEdge(dut.clk)
      dut._log.info(" Code: %s" % dut.code.value.binstr)
      dut._log.info(" State: %d" % dut.state.value.integer)

    # Check we unlocked the lock
    if dut.unlocked.value.integer == 1:
      dut._log.info("REACHED FINAL STATE!")
      return

    # Reset the DUT
    await reset_dut(dut.reset_n, 50)
