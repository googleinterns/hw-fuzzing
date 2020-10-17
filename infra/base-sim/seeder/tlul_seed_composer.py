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
import subprocess
import sys

import prettytable
import yaml

from opcode import (ENDIANNESS, OPCODE_SIZE, RW_OPCODE_THRESHOLD,
                    WAIT_OPCODE_THRESHOLD)

# Max field sizes for OT TLUL bus implementation
OT_TLUL_ADDR_SIZE = 4
OT_TLUL_DATA_SIZE = 4


def _red(s):
  return "\033[1m\033[91m{}\033[00m".format(s)


def _green(s):
  return "\033[1m\033[92m{}\033[00m".format(s)


def _yellow(s):
  return "\033[93m{}\033[00m".format(s)


def write_bytes(out_file, value, size_bytes):
  """Writes an integer value in binary to a file."""
  if value < 2**(size_bytes * 8):
    out_file.write(
        int(value).to_bytes(size_bytes, byteorder=ENDIANNESS, signed=False))
  else:
    print(_red("ERROR: value is too large for corresponding field. ABORTING!"))
    sys.exit(1)


def dump_seed_file_to_stdin(args):
  """Dumps generated seed file in hex format to STDIN."""
  print(args.output_filename + ":")
  cmd = ["xxd", args.output_filename]
  try:
    subprocess.check_call(cmd)
  except subprocess.CalledProcessError:
    print(_red("ERROR: cannot dump generated seed file."))
    sys.exit(1)


def generate_afl_seed(args):
  """Parse YAML HW fuzzing opcodes and translates them in binary to file."""
  print(f"Creating fuzzer seed from YAML: {args.input_filename} ...")
  # TODO(ttrippe): support various frame types and direct input bits
  with open(args.input_filename, "r") as in_file:
    fuzz_opcodes = yaml.load(in_file, Loader=yaml.Loader)
  with open(args.output_filename, "wb") as out_file:
    for instr in fuzz_opcodes:
      # Read HW fuzz instruction
      opcode, addr, data = instr.values()
      if args.verbose:
        print("Opcode: ", opcode)
        print("Address: 0x{:0>8X}".format(addr))
        print("Data:    0x{:0>8X}".format(data))
        print("-------------------")
      # Translate instruction to binary
      if opcode == "wait":
        write_bytes(out_file, 1, args.opcode_size)
      elif opcode == "write":
        write_bytes(out_file, WAIT_OPCODE_THRESHOLD, args.opcode_size)
        write_bytes(out_file, addr, args.address_size)
        write_bytes(out_file, data, args.data_size)
      elif opcode == "read":
        write_bytes(out_file, RW_OPCODE_THRESHOLD, args.opcode_size)
        write_bytes(out_file, addr, args.address_size)
      else:
        print("ERROR: invalid opcode in input file. ABORTING!")
        sys.exit(1)
  print(_green("Seed file generated!"))
  if args.verbose:
    dump_seed_file_to_stdin(args)


def _print_configs(args):
  # Create table to print configurations to STDIN
  config_table = prettytable.PrettyTable(header=False)
  config_table.title = "Seed Generation Parameters"
  config_table.field_names = ["Parameter", "Value"]

  # Add parameter values to table
  config_table.add_row(["Input (YAML) Filename", args.input_filename])
  config_table.add_row(["Output Filename", args.output_filename])
  config_table.add_row(["Frame Type", args.frame_type])
  config_table.add_row(["Opcode Size (# bytes)", args.opcode_size])
  config_table.add_row(["Address Size (# bytes)", args.address_size])
  config_table.add_row(["Data Size (# bytes)", args.data_size])

  # Print table
  config_table.align = "l"
  print(_yellow(config_table.get_string()))


def _main(argv):
  # Parse cmd args
  module_description = "OpenTitan Fuzzing Seed Composer"
  parser = argparse.ArgumentParser(description=module_description)
  parser.add_argument("--frame-type",
                      default="mapped-variable",
                      choices=[
                          "mapped-variable", "mapped-fixed",
                          "constant-variable", "constant-fixed"
                      ],
                      type=str,
                      help="Fuzzing instruction frame size and configuration.")
  parser.add_argument("--opcode-size",
                      default=OPCODE_SIZE,
                      type=int,
                      help="Size of opcode field in bytes.")
  parser.add_argument("--address-size",
                      default=OT_TLUL_ADDR_SIZE,
                      type=int,
                      help="Size of address field in bytes")
  parser.add_argument("--data-size",
                      default=OT_TLUL_DATA_SIZE,
                      type=int,
                      help="Size of data field in bytes.")
  # TODO(ttrippel): add argument to store direct external input bits
  parser.add_argument("-v",
                      "--verbose",
                      action="store_true",
                      help="Yes to all prompts.")
  parser.add_argument("input_filename",
                      metavar="input.yaml",
                      help="Input configuration YAML file.")
  parser.add_argument("output_filename",
                      metavar="afl_seed.tf",
                      help="Name of output seed file (hex).")
  args = parser.parse_args(argv)
  if args.verbose:
    _print_configs(args)

  # Generate output seed file
  generate_afl_seed(args)


if __name__ == "__main__":
  _main(sys.argv[1:])
