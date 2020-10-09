#!/usr/bin/python3
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

import argparse
import sys

import yaml

# Import custom cocotb extension packages
sys.path.append("/Users/ttrippel/repos/hw-fuzzing/hw/tb")
from cocotb_ext.hw_fuzz_opcode import (ENDIANNESS, OPCODE_SIZE,
                                       RW_OPCODE_THRESHOLD,
                                       WAIT_OPCODE_THRESHOLD)

# Max field sizes for OT TLUL bus implementation
OT_TLUL_ADDR_SIZE = 4
OT_TLUL_DATA_SIZE = 4


def write_bytes(out_file, value, size_bytes):
  """Writes an integer value in binary to a file."""
  if value < 2**(size_bytes * 8):
    out_file.write(
        int(value).to_bytes(size_bytes, byteorder=ENDIANNESS, signed=False))
  else:
    print("ERROR: value is too large for corresponding field. ABORTING!")
    sys.exit(1)


def generate_afl_seed(input_filename, output_filename):
  """Parse YAML HW fuzzing opcodes and translates them in binary to file."""
  with open(input_filename, "r") as in_file:
    fuzz_opcodes = yaml.load(in_file)
  with open(output_filename, "wb") as out_file:
    for instr in fuzz_opcodes:
      # Read HW fuzz instruction
      opcode, addr, data = instr.values()
      print("Opcode:", opcode)
      print("Address:", addr)
      print("Data:", data)
      # Translate instruction to binary
      if opcode == "wait":
        write_bytes(out_file, 1, OPCODE_SIZE)
      elif opcode == "write":
        write_bytes(out_file, WAIT_OPCODE_THRESHOLD, OPCODE_SIZE)
        write_bytes(out_file, addr, OT_TLUL_ADDR_SIZE)
        write_bytes(out_file, data, OT_TLUL_DATA_SIZE)
      elif opcode == "read":
        write_bytes(out_file, RW_OPCODE_THRESHOLD, OPCODE_SIZE)
        write_bytes(out_file, addr, OT_TLUL_ADDR_SIZE)
      else:
        print("ERROR: invalid opcode in input file. ABORTING!")
        sys.exit(1)


def main(argv):
  # Parse cmd args
  module_description = "OpenTitan Fuzzing Seed Composer"
  parser = argparse.ArgumentParser(description=module_description)
  # parser.add_argument("-",
  # "--yes",
  # action="store_true",
  # help="Yes to all prompts.")
  # TODO(ttrippel): add frame type option
  # TODO(ttrippel): add opcode size option
  # TODO(ttrippel): add address size option
  # TODO(ttrippel): add data size option
  parser.add_argument("config_filename",
                      metavar="config.yaml",
                      help="Input configuration YAML file.")
  parser.add_argument("output_filename",
                      metavar="ouput.tf",
                      help="Name of output seed file (hex).")
  args = parser.parse_args(argv)

  # Generate output seed file
  generate_afl_seed(args.config_filename, args.output_filename)


if __name__ == "__main__":
  main(sys.argv[1:])
