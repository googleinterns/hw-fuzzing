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

from hwfutils.string_color import color_str_green as green
from hwfutils.string_color import color_str_red as red
from hwfutils.string_color import color_str_yellow as yellow
from hwfutils.tlul_fuzz_instr import TLULFuzzInstr


def dump_seed_file_to_stdin(args):
  """Dumps generated seed file in hex format to STDIN."""
  print(args.output_filename + ":")
  cmd = ["xxd", args.output_filename]
  try:
    subprocess.check_call(cmd)
  except subprocess.CalledProcessError:
    print(red("ERROR: cannot dump generated seed file."))
    sys.exit(1)


def gen_seed(args):
  """Parse YAML HW fuzzing opcodes and translates them in binary to file."""
  print(f"Creating fuzzer seed from YAML: {args.input_filename} ...")
  with open(args.input_filename, "r") as in_file:
    fuzz_opcodes = yaml.load(in_file, Loader=yaml.Loader)
  with open(args.output_filename, "wb") as out_file:
    for instr in fuzz_opcodes:
      hwf_instr = TLULFuzzInstr(args, instr)
      if args.verbose:
        print(hwf_instr)
      for _ in range(hwf_instr.repeat):
        out_file.write(hwf_instr.to_bytes(args))
  print(green("Seed file generated!"))
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
  print(yellow(config_table.get_string()))


def _main(argv):
  # Parse cmd args
  module_description = "OpenTitan Fuzzing Seed Composer"
  parser = argparse.ArgumentParser(description=module_description)
  parser.add_argument("--opcode-type",
                      default="constant",
                      choices=[
                          "constant",
                          "mapped",
                      ],
                      type=str,
                      help="Fuzzing instruction opcode type.")
  parser.add_argument("--instr-type",
                      default="variable",
                      choices=[
                          "fixed",
                          "variable",
                      ],
                      type=str,
                      help="Fuzzing instruction frame type.")
  parser.add_argument("--endianness",
                      default=TLULFuzzInstr.default_endianness,
                      choices=[
                          "little",
                          "big",
                      ],
                      type=str,
                      help="Endianness of HW Fuzzing Instruction frames.")
  parser.add_argument("--opcode-size",
                      default=TLULFuzzInstr.default_opcode_size,
                      type=int,
                      help="Size of opcode field in bytes.")
  parser.add_argument("--address-size",
                      default=TLULFuzzInstr.default_address_size,
                      type=int,
                      help="Size of address field in bytes")
  parser.add_argument("--data-size",
                      default=TLULFuzzInstr.default_data_size,
                      type=int,
                      help="Size of data field in bytes.")
  parser.add_argument("--direct-in-size",
                      default=0,
                      type=int,
                      help="Size of direct inputs field in bytes.")
  parser.add_argument("-v",
                      "--verbose",
                      action="store_true",
                      help="Yes to all prompts.")
  parser.add_argument("input_filename",
                      metavar="input.yaml",
                      help="Input configuration YAML file.")
  parser.add_argument("output_filename",
                      metavar="afl_seed.hwf",
                      help="Name of output seed file (hex).")
  args = parser.parse_args(argv)
  if args.verbose:
    _print_configs(args)

  # Generate output seed file
  gen_seed(args)


if __name__ == "__main__":
  _main(sys.argv[1:])
