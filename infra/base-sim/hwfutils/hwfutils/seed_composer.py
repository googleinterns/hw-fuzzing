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


def dump_seed_file_to_stdin(output_file_name):
  """Dumps generated seed file in hex format to STDIN."""
  print(output_file_name + ":")
  cmd = ["xxd", output_file_name]
  try:
    subprocess.check_call(cmd)
  except subprocess.CalledProcessError:
    print(red("ERROR: cannot dump generated seed file."))
    sys.exit(1)


def gen_seed(input_yaml_file_name, output_file_name, verbose):
  """Parse YAML HW fuzzing opcodes and translates them in binary to file."""
  print(f"Creating fuzzer seed from YAML: {input_yaml_file_name} ...")
  with open(input_yaml_file_name, "r") as fp:
    fuzz_opcodes = yaml.load(fp, Loader=yaml.Loader)
  with open(output_file_name, "wb") as fp:
    for instr in fuzz_opcodes:
      hwf_instr = TLULFuzzInstr(instr)
      if verbose:
        print(hwf_instr)
      fp.write(hwf_instr.to_bytes())
  print(green("Seed file generated!"))
  if verbose:
    dump_seed_file_to_stdin(output_file_name)


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


def parse_args(argv):
  module_description = "OpenTitan Fuzzing Seed Composer"
  parser = argparse.ArgumentParser(description=module_description)
  parser.add_argument("--opcode-type",
                      default=TLULFuzzInstr.opcode_type,
                      choices=[
                          "constant",
                          "mapped",
                      ],
                      type=str,
                      help="Fuzzing instruction opcode type.")
  parser.add_argument("--instr-type",
                      default=TLULFuzzInstr.instr_type,
                      choices=[
                          "fixed",
                          "variable",
                      ],
                      type=str,
                      help="Fuzzing instruction frame type.")
  parser.add_argument("--endianness",
                      default=TLULFuzzInstr.endianness,
                      choices=[
                          "little",
                          "big",
                      ],
                      type=str,
                      help="Endianness of HW Fuzzing Instruction frames.")
  parser.add_argument("--opcode-size",
                      default=TLULFuzzInstr.opcode_size,
                      type=int,
                      help="Size of opcode field in bytes.")
  parser.add_argument("--address-size",
                      default=TLULFuzzInstr.address_size,
                      type=int,
                      help="Size of address field in bytes")
  parser.add_argument("--data-size",
                      default=TLULFuzzInstr.data_size,
                      type=int,
                      help="Size of data field in bytes.")
  parser.add_argument("--direct-in-size",
                      default=TLULFuzzInstr.direct_in_size,
                      type=int,
                      help="Size of direct inputs field in bytes.")
  parser.add_argument("-v",
                      "--verbose",
                      action="store_true",
                      help="Enable verbose status messages.")
  parser.add_argument("input_file_name",
                      metavar="input.yaml",
                      help="Input configuration YAML file.")
  parser.add_argument("output_file_name",
                      metavar="afl_seed.hwf",
                      help="Name of output seed file (hex).")
  args = parser.parse_args(argv)
  if args.verbose:
    _print_configs(args)
  return args


def config_tlul_fuzz_instr(args):
  TLULFuzzInstr.opcode_type = args.opcode_type
  TLULFuzzInstr.instr_type = args.instr_type
  TLULFuzzInstr.opcode_size = args.opcode_size
  TLULFuzzInstr.address_size = args.address_size
  TLULFuzzInstr.data_size = args.data_size
  TLULFuzzInstr.direct_in_size = args.direct_in_size
  TLULFuzzInstr.endianness = args.endianness


def main(argv):
  args = parse_args(argv)
  config_tlul_fuzz_instr(args)
  gen_seed(args.input_file_name, args.output_file_name, args.verbose)


if __name__ == "__main__":
  main(sys.argv[1:])
