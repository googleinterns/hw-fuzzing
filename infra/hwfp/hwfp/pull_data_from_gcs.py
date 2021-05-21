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
"""Helper module to interact with GCS.

Description:
This module implements a method to pull all data from a GCS bucket.
"""

import glob
import multiprocessing
import os
import subprocess
import sys

import hjson
from hwfutils.run_cmd import run_cmd


def pull_data_from_gcs(search_prefix=None):
  """Pulls down fuzzer data from GCS to local machine."""
  # Create worker pool
  pool = multiprocessing.Pool(None)

  # Check if local DST path exists first, if not, create it
  parent_dst = os.path.join(os.getenv("HW_FUZZING"), "data")
  if not os.path.exists(parent_dst):
    os.makedirs(parent_dst)

  # Get list of experiment result directories stored in GCS fuzzing-data bucket
  gcs_bucket_path = _get_gcs_bucket_path()
  ls_cmd = ["gsutil", "ls", gcs_bucket_path]
  proc = subprocess.Popen(ls_cmd,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          close_fds=True)
  while True:
    line = proc.stdout.readline()
    if not line:
      break
    src = line.decode("utf-8").rstrip("/\n")
    dst = os.path.join(parent_dst, os.path.basename(src))
    if (search_prefix is None or
        search_prefix in src) and not _data_exists_locally(dst):
      print("Pulling down fuzzing data from %s ..." % src)
      # Just copy the files we need (coverage/stats files)
      cp_cmds = []
      data_files = _get_data_file_paths(src)
      for df in data_files:
        cp_cmds.append(
            ["gsutil", "cp",
             os.path.join(src, df),
             os.path.join(dst, df)])
        results = pool.map_async(_run_gsutil_cmd, cp_cmds)
        results.wait()


def _get_data_file_paths(src):
  data_files = ["out/%s/plot_data" % _get_afl_plot_file_path(src)]
  log_files = [
      "exp.log", "fuzz_time.log", "svas.csv", "bb_complexity.csv",
      "kcov_cum.csv", "llvm_cov_cum.csv", "vlt_cov_cum.csv"
  ]
  for lf in log_files:
    data_files.append(os.path.join("logs", lf))
  return data_files


def _get_afl_plot_file_path(src):
  ls_cmd = ["gsutil", "ls", os.path.join(src, "out")]
  proc = subprocess.Popen(ls_cmd,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          close_fds=True)
  line = proc.stdout.readline().decode("utf-8").rstrip("\n /")
  return os.path.basename(line)


def _run_gsutil_cmd(gs_util_cmd):
  run_cmd(gs_util_cmd,
          "ERROR: cannot copy data from GCS.",
          silent=True,
          fail_silent=True)


def _get_gcs_bucket_path():
  gcp_config_filename = os.getenv("HW_FUZZING") + "/gcp_config.hjson"
  with open(gcp_config_filename, "r") as hjson_file:
    gcp_configs = hjson.load(hjson_file)
  return "gs://%s-%s" % (gcp_configs["project_id"], gcp_configs["data_bucket"])


def _data_exists_locally(exp_data_path):
  """Checks if local experiment data already exists."""
  if glob.glob(exp_data_path):
    return True
  return False


if __name__ == "__main__":
  if len(sys.argv) < 2 or sys.argv[1] == "":
    pull_data_from_gcs()
  else:
    pull_data_from_gcs(search_prefix=sys.argv[1])
