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
from enum import IntEnum

import prettytable

from hwfutils.string_color import color_str_red as red


class TLULOpcode(IntEnum):
  """Hardware fuzzing opcode for fuzzing TL-UL driven cores."""
  invalid = 0
  wait = 1
  read = 2
  write = 3


class _YAMLTags:
  opcode = "opcode"
  address = "addr"
  data = "data"
  direct_in = "direct-in"
  repeat = "repeat"


class TLULFuzzInstr:
  default_opcode_size = 1
  default_address_size = 4
  default_data_size = 4
  default_endianness = "little"

  def __init__(self, args, instr):
    # init attributes
    self.opcode_str = "invalid"
    self.opcode = TLULOpcode.invalid
    self.address = 0
    self.data = 0
    self.direct_in = None
    self.repeat = 1

    # Validate/Decode opcode string
    if _YAMLTags.opcode not in instr:
      print(red("ERROR: all YAML lines require an opcode field. ABORTING!"))
    self.opcode_str = str(instr[_YAMLTags.opcode])
    self.opcode = self._decode_opcode_str()

    # Check ADDRESS and DATA fields exist in YAML and convert to int
    if self.opcode == TLULOpcode.read:
      if _YAMLTags.address not in instr:
        print(red("ERROR: read opcodes require an ADDRESS field. ABORTING!"))
        sys.exit(1)
      self.address = int(instr[_YAMLTags.address])
    elif self.opcode == TLULOpcode.write:
      if _YAMLTags.address not in instr:
        print(red("ERROR: write opcodes require an ADDRESS field. ABORTING!"))
        sys.exit(1)
      if _YAMLTags.data not in instr:
        print(red("ERROR: write opcodes require an DATA field. ABORTING!"))
        sys.exit(1)
      self.address = int(instr[_YAMLTags.address])
      self.data = int(instr[_YAMLTags.data])

    # Validata address and data fields
    self._validate_instr_field_size(_YAMLTags.address, self.address,
                                    args.address_size)
    self._validate_instr_field_size(_YAMLTags.data, self.data, args.data_size)

    # check if DIRECT_IN should exist in YAML and convert to int
    if args.direct_in_size > 0:
      if _YAMLTags.direct_in not in instr:
        print(red("ERROR: direct_in field required if size > 0. ABORTING!"))
      else:
        self.direct_in = int(instr[_YAMLTags.direct_in])
        self._validate_instr_field_size(_YAMLTags.direct_in, self.direct_in,
                                        args.direct_in_size)

    # check if REPEAT field exists in YAML and convert to int
    if _YAMLTags.repeat in instr:
      self.repeat = int(instr[_YAMLTags.repeat])

  def __str__(self):
    instr_table = prettytable.PrettyTable(header=False)
    instr_table.title = "HW Fuzzing Instruction"
    instr_table.field_names = ["Field", "Value"]
    instr_table.add_row = (["Opcode", self.opcode_str])
    instr_table.add_row = (["Address", "0x{:0>8X}".format(self.address)])
    instr_table.add_row = (["Data", "0x{:0>8X}".format(self.data)])
    instr_table.add_row = (["Direct In", "0x{:0>8X}".format(self.direct_in)])
    instr_table.add_row = (["Repeat", self.repeat])
    instr_table.align = "l"
    return instr_table.get_string()

  def _decode_opcode_str(self):
    if self.opcode_str == "wait":
      return TLULOpcode.wait
    elif self.opcode_str == "read":
      return TLULOpcode.read
    elif self.opcode_str == "write":
      return TLULOpcode.write
    else:
      print("ERROR: invalid opcode (%s) encountered. ABORTING!" %
            self.opcode_str)
      sys.exit(1)

  def _validate_instr_field_size(self, field, value, size):
    if value >= 2**(size * 8):
      print(
          red("ERROR: instruction field (%s) larger than size. ABORTING!" %
              field))
      sys.exit(1)

  def _opcode2int(self, args):
    if args.opcode_type == "constant":
      # Opcode is mapped to a fixed value
      opcode_int = int(self.opcode)
    else:
      # Opcode is mapped to a range
      max_opcode_value = 2**(args.opcode_size * 8)
      num_opcodes = len(TLULOpcode)
      opcode_int = (self.opcode - 1) * int(max_opcode_value / num_opcodes) + 1
    return opcode_int

  def to_bytes(self, args):
    # create OPCODE bytes from integer
    opcode_int = self._opcode2int(args)
    opcode_bytes = opcode_int.to_bytes(args.opcode_size,
                                       byteorder=args.endianness,
                                       signed=False)
    # create DATA bytes from integer value
    address_bytes = self.address.to_bytes(args.address_size,
                                          byteorder=args.endianness,
                                          signed=False)
    # create DATA bytes from integer value
    data_bytes = self.data.to_bytes(args.data_size,
                                    byteorder=args.endianness,
                                    signed=False)
    # create DIRECT_INTPUTS bytes from integer value (if any exist)
    if self.direct_in is not None:
      direct_in_bytes = self.direct_in.to_bytes(args.direct_in_size,
                                                byteorder=args.endianness,
                                                signed=False)

    # Build the instruction frame
    if args.instr_type == "fixed":
      if self.direct_in is not None:
        return opcode_bytes + address_bytes + data_bytes + direct_in_bytes
      else:
        return opcode_bytes + address_bytes + data_bytes
    else:
      if self.direct_in is not None:
        # Include DIRECT_IN bits in instruction
        if self.opcode == TLULOpcode.wait:
          return opcode_bytes + direct_in_bytes
        elif self.opcode == TLULOpcode.read:
          return opcode_bytes + address_bytes + direct_in_bytes
        else:
          return opcode_bytes + address_bytes + data_bytes + direct_in_bytes
      else:
        # DO NOT include DIRECT_IN bits in instruction
        if self.opcode == TLULOpcode.wait:
          return opcode_bytes
        elif self.opcode == TLULOpcode.read:
          return opcode_bytes + address_bytes
        else:
          return opcode_bytes + address_bytes + data_bytes
