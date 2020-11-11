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
import errno
import glob
import itertools
import os
import shutil
import sys
import threading
import time

import hjson
from hwfp.fuzz import fuzz
from hwfutils.string_color import color_str_green as green
from hwfutils.string_color import color_str_red as red

OPCODE_TYPES = ["constant", "mapped"]
INSTR_TYPES = ["variable", "fixed"]
TERMINATE_TYPES = ["invalidop", "never"]

HJSON_CONFIG_TEMPLATE = "tests/aes_test_template.hjson"
TMP_HJSON_CONFIG = "tmp.hjson"
ENCRYPT_LOG = "encrypt.results.txt"
DECRYPT_LOG = "decrypt.results.txt"

TERMINAL_ROWS, TERMINAL_COLS = os.popen('stty size', 'r').read().split()
LINE_SEP = "=" * int(TERMINAL_COLS)
TEST_IS_EXECUTING = False


class AESTestParams:
  def __init__(self, num_crypts, data_block_size, data_in_line_starts,
               data_out_line_starts):
    self.num_crypts = num_crypts
    self.data_block_size = data_block_size
    self.data_in_line_starts = data_in_line_starts
    self.data_out_line_starts = data_out_line_starts

  def __eq__(self, x):
    if (self.num_crypts == x.num_crypts and
        self.data_block_size == x.data_block_size and
        len(self.data_in_line_starts) == len(x.data_in_line_starts) and
        len(self.data_out_line_starts) == len(x.data_out_line_starts)):
      return True
    else:
      return False

  def __ne__(self, x):
    if self == x:
      return False
    else:
      return True


class AESTest:
  def __init__(self, mode, hwf_seed, params):
    self.mode = mode
    self.hwf_seed = hwf_seed.replace(".yml", ".hwf", 1)
    self.num_crypts = params.num_crypts
    self.data_block_size = params.data_block_size
    self.data_in_line_starts = params.data_in_line_starts
    self.data_out_line_starts = params.data_out_line_starts


class AESTestPair:
  def __init__(self, encrypt_test, decrypt_test):
    self.encrypt = encrypt_test
    self.decrypt = decrypt_test
    self.test_id = self.encrypt.hwf_seed.split(".")[0].replace(
        "encrypt", "x", 1)


def _waiting_animation():
  for c in itertools.cycle(['|', '/', '-', '\\']):
    if not TEST_IS_EXECUTING:
      break
    print("\rexecuting " + c, end="")
    sys.stdout.flush()
    time.sleep(0.5)


def _get_next_test_param(yaml_seed, yaml_seed_file, expected_key):
  line = yaml_seed_file.readline()
  line_list = line.lstrip("# ").rstrip().split("=")
  key = line_list[0]
  if key != expected_key:
    print(red("ERROR: expected test parameter (%s) not in YAML seed (%s)." %
              (expected_key, yaml_seed)),
          file=sys.stderr)
    sys.exit(1)
  return int(line_list[1])


def _extract_crypt_io_log_lines(yaml_seeds_dir, yaml_seed):
  num_crypts = 0
  data_block_size = 0
  data_in_line_starts = []
  data_out_line_starts = []
  with open(os.path.join(yaml_seeds_dir, yaml_seed), "r") as ys:
    for line in ys:
      line = line.rstrip().lstrip("# ")
      if line == "TEST VARIABLES":
        ys.readline()
        # subtract three to account for other text in log
        num_crypts = _get_next_test_param(yaml_seed, ys, "NUM_CRYPTS")
        data_block_size = _get_next_test_param(yaml_seed, ys,
                                               "DATA_BLOCK_SIZE")
        for crypt_num in range(1, num_crypts + 1):
          data_in_line_starts.append(
              _get_next_test_param(yaml_seed, ys, "DATA_IN_LINE_START_" +
                                   str(crypt_num)) - 3)
          data_out_line_starts.append(
              _get_next_test_param(yaml_seed, ys, "DATA_OUT_LINE_START_" +
                                   str(crypt_num)) - 3)
  if (num_crypts == 0 or data_block_size == 0 or
      len(data_in_line_starts) == 0 or len(data_out_line_starts) == 0):
    print(red("ERROR: could not retrieve test params from YAML seed (%s)." %
              yaml_seed),
          file=sys.stderr)
    sys.exit(1)
  return AESTestParams(num_crypts, data_block_size, data_in_line_starts,
                       data_out_line_starts)


def _extract_test_pairs(yaml_seeds_dir, testcase=None):
  test_pairs = []
  encrypt_seeds = glob.glob(os.path.join(yaml_seeds_dir, "*encrypt*.yml"))
  decrypt_seeds = glob.glob(os.path.join(yaml_seeds_dir, "*decrypt*.yml"))
  encrypt_seeds = list(map(os.path.basename, encrypt_seeds))
  decrypt_seeds = list(map(os.path.basename, decrypt_seeds))
  encrypt_seeds.sort()
  decrypt_seeds.sort()
  if len(encrypt_seeds) != len(decrypt_seeds):
    print(red("ERROR: non-symmetric number of encrypt/decrypt seeds."),
          file=sys.stderr)
    sys.exit(1)
  for i in range(len(encrypt_seeds)):
    if testcase is not None:
      prefix = testcase.split("x")[0]
      suffix = "".join([testcase.split("x")[-1], ".yml"])
      if (not encrypt_seeds[i].startswith(prefix) or
          not encrypt_seeds[i].endswith(suffix)):
        continue
    # Extract test details from comments in yaml file
    encrypt_test_params = _extract_crypt_io_log_lines(yaml_seeds_dir,
                                                      encrypt_seeds[i])
    decrypt_test_params = _extract_crypt_io_log_lines(yaml_seeds_dir,
                                                      decrypt_seeds[i])
    # Check if the test params are equivalent
    if encrypt_test_params != decrypt_test_params:
      print(red("ERROR: test parameters do not match for seeds (%s and %s)." %
                (encrypt_seeds[i], decrypt_seeds[i])),
            file=sys.stderr)
      sys.exit(1)
    # Create test objects and pair them together
    encrypt_test = AESTest("encrypt", encrypt_seeds[i], encrypt_test_params)
    decrypt_test = AESTest("decrypt", decrypt_seeds[i], decrypt_test_params)
    test_pairs.append(AESTestPair(encrypt_test, decrypt_test))
  return test_pairs


def _load_config_template(hjson_config_template):
  config_dict = None
  with open(hjson_config_template, "r") as hjson_file:
    config_dict = hjson.load(hjson_file)
  return config_dict


def _extract_data_from_lines(line):
  return int(line.rstrip().split(":")[-1].lstrip(), 16)


def _get_crypt_io_data_blocks(logs, start_line, num_lines):
  data_block_lines = logs[start_line:][:num_lines]
  data_blocks = list(map(_extract_data_from_lines, data_block_lines))
  return data_blocks


def _set_isa_params(config_template, opcode_type, instr_type, terminate_type):
  # Load config dict from template
  config_dict = _load_config_template(config_template)
  # Set params
  config_dict["model_params"]["opcode_type"] = opcode_type
  config_dict["model_params"]["instr_type"] = instr_type
  if terminate_type == "invalidop":
    config_dict["model_params"]["terminate_on_invalid_opcode"] = 1
  else:
    config_dict["model_params"]["terminate_on_invalid_opcode"] = 0
  return config_dict


def _run_simulation(config_dict, output_log_file_name, aes_test):
  # Get path of experiment log file
  exp_log = os.path.join(os.getenv("HW_FUZZING"), "data",
                         config_dict["experiment_name"], "logs", "exp.log")
  # Set correct seed file
  config_dict["fuzzer_params"]["seed"] = aes_test.hwf_seed
  # Write configs to a temp HJSON file
  with open(TMP_HJSON_CONFIG, "w") as fp:
    hjson.dump(config_dict, fp)
  # Run encrypt test in HWFP
  fuzz(["-y", "--log-driver", "none", "-s", TMP_HJSON_CONFIG])
  shutil.copy(exp_log, output_log_file_name)


def _check_simulation_results(encrypt_results, decrypt_results, test_pair):
  error = False
  for i in range(len(test_pair.encrypt.data_in_line_starts)):
    # Extract plaintexts/ciphertexts
    with open(encrypt_results, "r") as fp:
      log_lines = fp.readlines()
      encrypt_in_data = _get_crypt_io_data_blocks(
          log_lines, test_pair.encrypt.data_in_line_starts[i],
          test_pair.encrypt.data_block_size)
      encrypt_out_data = _get_crypt_io_data_blocks(
          log_lines, test_pair.encrypt.data_out_line_starts[i],
          test_pair.encrypt.data_block_size)
    with open(decrypt_results, "r") as fp:
      log_lines = fp.readlines()
      decrypt_in_data = _get_crypt_io_data_blocks(
          log_lines, test_pair.decrypt.data_in_line_starts[i],
          test_pair.decrypt.data_block_size)
      decrypt_out_data = _get_crypt_io_data_blocks(
          log_lines, test_pair.decrypt.data_out_line_starts[i],
          test_pair.decrypt.data_block_size)
    # Check all data blocks are the same length
    if (len(encrypt_in_data) != len(encrypt_out_data) or
        len(encrypt_in_data) != len(decrypt_in_data) or
        len(encrypt_in_data) != len(decrypt_out_data)):
      error = True
      error_msg = "data LENGTH MISMATCH for encrypt/decrypt data blocks."
      # break
    # Check inputs/outputs of encrypt/decrypt match
    if not error:
      for i in range(len(encrypt_out_data)):
        print("   Encrypt Out =  0x{:0>8X}; Decrypt In = 0x{:0>8X}".format(
            encrypt_out_data[i], decrypt_in_data[i]))
        if encrypt_out_data[i] != decrypt_in_data[i]:
          error_msg = "encryption OUTPUT does not match decryption INPUT."
          error = True
          break
    print("   --------------------------------------------")
    if not error:
      for i in range(len(encrypt_in_data)):
        print("   Encrypt In =  %d; Decrypt Out = %d" %
        print("   Encrypt In =  0x{:0>8X}; Decrypt Out = 0x{:0>8X}".format(
              encrypt_in_data[i], decrypt_out_data[i]))
        if encrypt_in_data[i] != decrypt_out_data[i]:
          error_msg = "encryption INPUT does not match decryption OUTPUT."
          break
    print("   --------------------------------------------")
    # If an error occured during any test, terminate
    if error:
      break
  # Print a color-coded message with results
  if not error:
    print(green("PASS"))
  else:
    print("".join([red("ERROR"), ":", error_msg]))


def _main(argv):
  # Part command line arguments
  parser = argparse.ArgumentParser(description="AES Smoke Test")
  parser.add_argument(
      "-t",
      "--testcase",
      default=None,
      help="Specific testcase to run, otherwise all tests are run.")
  args = parser.parse_args(argv)

  # Print initial message with # of total tests
  isas = list(itertools.product(OPCODE_TYPES, INSTR_TYPES, TERMINATE_TYPES))
  num_tests = len(isas)
  print(LINE_SEP)
  print(green("Running %d test suites ..." % num_tests))

  # Get list of encryption/decryption test pairs
  yaml_descripts_dir = os.path.join(os.getenv("HW_FUZZING"), "hw", "aes",
                                    "seed_descriptions")
  test_pairs = _extract_test_pairs(yaml_descripts_dir, args.testcase)

  test_suite_num = 1
  for opcode_type, instr_type, terminate_type in isas:
    print(LINE_SEP)
    print("Test Suite #:    ", test_suite_num)
    print("Opcode Type:     ", opcode_type)
    print("Instruction Type:", instr_type)
    print("Termination Type:", terminate_type)
    print(LINE_SEP)

    # Set ISA parameters
    config_dict = _set_isa_params(HJSON_CONFIG_TEMPLATE, opcode_type,
                                  instr_type, terminate_type)

    # Perform E2E encryption/decryption simulation tests on OpenTitan AES block
    for tp in test_pairs:
      try:
        print("(%s)\t- " % tp.test_id, end="")
        sys.stdout.flush()

        # Run simulations in separate thread to show animated waiting spinner
        # TEST_IS_EXECUTING = True
        # t = threading.Thread(target=_waiting_animation)
        # t.daemon = True
        # t.start()
        _run_simulation(config_dict, ENCRYPT_LOG, tp.encrypt)
        _run_simulation(config_dict, DECRYPT_LOG, tp.decrypt)
        # TEST_IS_EXECUTING = False

        # Check simulation results
        _check_simulation_results(ENCRYPT_LOG, DECRYPT_LOG, tp)

      finally:
        try:
          os.remove(TMP_HJSON_CONFIG)
          os.remove(ENCRYPT_LOG)
          os.remove(DECRYPT_LOG)
        except OSError as e:
          if e.errno != errno.ENOENT:
            raise
    test_suite_num += 1


if __name__ == "__main__":
  _main(sys.argv[1:])
