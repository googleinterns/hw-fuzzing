# Copyright 2020 Timothy Trippel
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

import sys

import pytest
from hwfutils.tlul_fuzz_instr import TLULFuzzInstr, TLULOpcode


def gen_hwf_yaml_instr(opcode_str, addr, data, repeat=0):
  if repeat > 1:
    return {"opcode": opcode_str, "addr": addr, "data": data, "repeat": repeat}
  else:
    return {"opcode": opcode_str, "addr": addr, "data": data}


@pytest.mark.parametrize("opcode_str", [
    "wait", "read", "write",
    pytest.param("invalid", marks=pytest.mark.xfail)
])
@pytest.mark.parametrize("addr", [0])
@pytest.mark.parametrize("data", [0])
def test_init_opcode(opcode_str, addr, data):
  hwf_yaml_instr = gen_hwf_yaml_instr(opcode_str, addr, data)
  hwf_instr = TLULFuzzInstr(hwf_yaml_instr)
  assert hwf_instr.opcode_str == hwf_yaml_instr["opcode"]
  if hwf_yaml_instr["opcode"] == "wait":
    assert hwf_instr.opcode == TLULOpcode.wait
  elif hwf_yaml_instr["opcode"] == "read":
    assert hwf_instr.opcode == TLULOpcode.read
  elif hwf_yaml_instr["opcode"] == "write":
    assert hwf_instr.opcode == TLULOpcode.write
  else:
    assert hwf_instr.opcode == TLULOpcode.invalid


@pytest.mark.parametrize("opcode_str", [
    "wait", "read", "write",
    pytest.param("invalid", marks=pytest.mark.xfail)
])
@pytest.mark.parametrize("addr", [0])
@pytest.mark.parametrize("data", [0])
@pytest.mark.parametrize("opcode_type", ["constant", "mapped"])
@pytest.mark.parametrize("instr_type", ["fixed"])
def test_to_bytes_opcode_type(opcode_type, instr_type, opcode_str, addr, data):
  # Configure TLULFuzzInstr
  TLULFuzzInstr.opcode_type = opcode_type
  TLULFuzzInstr.instr_type = instr_type

  # Generate YAML instruction format and construct TLULFuzzInstr
  hwf_yaml_instr = gen_hwf_yaml_instr(opcode_str, addr, data)
  hwf_instr = TLULFuzzInstr(hwf_yaml_instr)

  # Convert TLULFuzzInstr to an array of bytes
  hwf_instr_bytes = hwf_instr.to_bytes()

  # Compute correct bytes
  if opcode_type == "constant":
    if opcode_str == "wait":
      correct = hwf_instr_bytes[0] == 1
    elif opcode_str == "read":
      correct = hwf_instr_bytes[0] == 2
    elif opcode_str == "write":
      correct = hwf_instr_bytes[0] == 3
  else:
    if opcode_str == "wait":
      correct = hwf_instr_bytes[0] < 85
    elif opcode_str == "read":
      correct = 85 <= hwf_instr_bytes[0] < 170
    elif opcode_str == "write":
      correct = hwf_instr_bytes[0] >= 170

  # Test opcode is correct
  assert_msg = "TLUL opcode (%s - %d) is not in the correct range." % (
      opcode_str, hwf_instr_bytes[0])
  assert correct, assert_msg


@pytest.mark.parametrize("opcode_str", [
    "wait", "read", "write",
    pytest.param("invalid", marks=pytest.mark.xfail)
])
@pytest.mark.parametrize("addr", range(0, 5))
@pytest.mark.parametrize("data", range(0, 5))
@pytest.mark.parametrize("opcode_type", ["constant"])
@pytest.mark.parametrize("instr_type", ["fixed", "variable"])
def test_to_bytes_instr_type(opcode_type, instr_type, opcode_str, addr, data):
  # Configure TLULFuzzInstr
  TLULFuzzInstr.opcode_type = opcode_type
  TLULFuzzInstr.instr_type = instr_type

  # Generate YAML instruction format and construct TLULFuzzInstr
  hwf_yaml_instr = gen_hwf_yaml_instr(opcode_str, addr, data)
  hwf_instr = TLULFuzzInstr(hwf_yaml_instr)

  # Convert TLULFuzzInstr to an array of bytes
  hwf_instr_bytes = hwf_instr.to_bytes()

  # Compute correct length, address bytes, data bytes
  assert_msg = "TLUL instruction format is incorrect."
  if instr_type == "fixed":
    assert len(hwf_instr_bytes) == (TLULFuzzInstr.opcode_size +
                                    TLULFuzzInstr.address_size +
                                    TLULFuzzInstr.data_size), assert_msg
  # address_bytes = hwf_instr_bytes[TLULFuzzInstr.
  # opcode_size:TLULOpcode.opcode_size +
  # TLULFuzzInstr.address_size]
  # data_bytes = hwf_instr_bytes[TLULFuzzInstr.
  # opcode_size:TLULOpcode.opcode_size +
  # TLULFuzzInstr.data_size]
  else:
    if opcode_str == "wait":
      assert len(hwf_instr_bytes) == TLULFuzzInstr.opcode_size, assert_msg
    elif opcode_str == "read":
      assert len(hwf_instr_bytes) == (TLULFuzzInstr.opcode_size +
                                      TLULFuzzInstr.data_size), assert_msg
    elif opcode_str == "write":
      assert len(hwf_instr_bytes) == (TLULFuzzInstr.opcode_size +
                                      TLULFuzzInstr.address_size +
                                      TLULFuzzInstr.data_size), assert_msg
