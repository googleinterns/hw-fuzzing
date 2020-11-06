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
import os
import subprocess

import hjson
from hwfutils.run_cmd import run_cmd


def pull_data_from_gcs():
  """Pulls down fuzzer data from GCS to local machine."""
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
    dst = os.path.join(parent_dst, src.split("/")[-1])
    if not _data_exists_locally(dst):
      # TODO(ttrippel): speed up with -m option (causes issues on MacOS)
      # cp_cmd = ["gsutil", "-m", "cp", "-r", src, parent_dst]
      cp_cmd = ["gsutil", "cp", "-r", src, parent_dst]
      print("Pulling down fuzzing data from %s ..." % src)
      run_cmd(cp_cmd, "ERROR: cannot copy data from GCS.")


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
  pull_data_from_gcs()
