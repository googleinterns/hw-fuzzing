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

import glob
import json
import os
import sys
from vcdvcd import VCDVCD

def parse_vcd_symbol_dict(vcd_file):
    vcd_sig2symbol_dict = {}
    vcd = VCDVCD(vcd_file, only_sigs=True)
    vcd_data = vcd.get_data()
    for symbol in vcd_data.keys():
        for signal in vcd_data[symbol]['references']:
            vcd_sig2symbol_dict[signal] = symbol
    return vcd_sig2symbol_dict

def main(args):
    vcd_files_dir = args[0]
    json_output_filename = "data.json"
    signals = ["TOP.count_1[7:0]", "TOP.count_2[7:0]"]

    # Prep data dict
    data_dict = {}
    data_dict["Input File"] = []
    data_dict["Signal"] = []
    data_dict["Value"] = []

    # iterate over VCD files in dir
    input_file_num = 0

    # TODO: sort input files by time stamp? does AFLGO filename correlate?
    prev_cwd = os.getcwd()
    os.chdir(vcd_files_dir)
    vcd_files = glob.glob("*.vcd")

    for vcd_file in vcd_files:
        # Compute signal to symbol mapping
        vcd_sig2symbol_dict = parse_vcd_symbol_dict(vcd_file)

        # Extract last value expressed by signals in VCD file
        print("Extracting last value for signals in:", vcd_file)
        for sig in signals:
            # Extract last value expressed by signal in VCD file
            vcd_data = VCDVCD(vcd_file, signals=sig)
            vcd_sig_symbol = vcd_sig2symbol_dict[sig]
            last_value_str = vcd_data.get_data()[vcd_sig_symbol]['tv'][-1][1]
            last_value_int = int(last_value_str, 2)

            # Add data to dictionary in long format (easier for plotting)
            data_dict["Input File"].append(input_file_num)
            data_dict["Signal"].append(sig)
            data_dict["Value"].append(last_value_int)

        # Increment file number
        input_file_num += 1

    # Dump data to a JSON file for plotting
    with open(json_output_filename, 'w') as fp:
        json.dump(data_dict, fp)

    # Change back to orginal directory
    os.chdir(prev_cwd)

if __name__ == "__main__":
    main(sys.argv[1:])
