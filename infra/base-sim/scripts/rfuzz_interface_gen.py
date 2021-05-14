#!/usr/bin/python3
# Copyright 2021 Timothy Trippel
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
import os
import sys

import toml

template = """
// This file was generated from {conf_toml} using the dut_gen.py script.
// It contains DUT specific interface code for the verilator C++ test harness.

#ifndef RFUZZ_TB_INTERFACE_H_
#define RFUZZ_TB_INTERFACE_H_

#include "Vtop.h"

static constexpr size_t InputSize = {input_size};

static inline void apply_input(Vtop* top, const uint8_t* input) {{
{apply_input}
}}

#endif // RFUZZ_TB_INTERFACE_H_
"""

align = 8


def bits_to_size(bits):
  bytes = (bits + 7) // 8
  words = (bytes + align - 1) // align
  return words * align


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='generate DUT specific verilator code')
  parser.add_argument('-o',
                      '--output',
                      help='dut header file name',
                      required=True)
  parser.add_argument('-i',
                      '--input',
                      help='toml dut description',
                      required=True)
  args = parser.parse_args()

  conf_toml = args.input
  if not os.path.isfile(conf_toml):
    sys.stderr.write("dur config file `{}` not found\n".format(conf_toml))
    sys.exit(1)

  header = args.output
  header_dir = os.path.dirname(os.path.abspath(header))
  if not os.path.isdir(header_dir):
    sys.stderr.write(
        "output directory `{}` does not exist\n".format(header_dir))
    sys.exit(1)

  conf = toml.loads(open(conf_toml).read())
  input_bits = sum(ii['width'] for ii in conf['input'])
  input_size = bits_to_size(input_bits)

  i_line = "\ttop->io_input_bytes_{0: <3}  = input[{0: >3}];"
  dd = {
      'conf_toml': conf_toml,
      'toplevel': conf['general']['top'],
      'input_size': input_size,
      'apply_input': "\n".join(i_line.format(ii) for ii in range(input_size)),
  }

  output = template.format(**dd)
  open(header, 'w').write(output)
