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
"""This module contains methods to fuzz hw within containerized infrastructure.

Description:
This module contains several methods that:
1. Parse an HJSON configuration file defining which toplevel IP core to fuzz and
   how to fuzz it (e.g., see hw/aes/cpp_afl.hjson).
2. Builds a Docker image containing the DUT (toplevel) HDL, the desired
   testbench, fuzzer, Verilator (simulation engine), and compilation/simulation
   scripts).
3. Checks if data already exists/creates a directory to store the fuzzing
   results either locally or in a GCS bucket.
4. Launches a Docker container either locally or on a GCP VM to fuzz the DUT.

Usage Example:
  fuzz.py <HSJON configuration file>
"""

import argparse
import glob
import os
import shutil
import signal
import stat
import subprocess
import sys
import time

sys.path.append(os.path.join(os.getenv("HW_FUZZING"), "infra"))
from hwfp.config import LINE_SEP, Config
from hwfp.run_cmd import run_cmd
from hwfp.string_color import color_str_green as green
from hwfp.string_color import color_str_red as red
from hwfp.string_color import color_str_yellow as yellow

SEEDER_PATH = "infra/base-sim/seeder"
SHARED_TB_PATH = "infra/base-sim/tb"
MAX_NUM_VM_INSTANCES = 32  # this is max default quota for us-east4-a zone
VM_LAUNCH_WAIT_TIME_S = 30


# Abort this fuzzing session
def _abort(abort_msg):
    print(red(abort_msg))
    sys.exit(1)


# Handler to gracefully exit on ctrl+c
def _sigint_handler(sig, frame):
  print(red("\nTERMINATING EXPERIMENT!"))
  sys.exit(0)


# Verify an action with user input
def _verify_action(config, action, action_msg, abort_msg):
  if config.args.fail_silently:
    return True
  elif config.args.no:
    _abort(abort_msg)
  elif config.args.yes:
    action(config)
  else:
    ovw = input(yellow(action_msg))
    if ovw in {"yes", "y", "Y", "YES", "Yes", ""}:
      action(config)
    else:
      _abort(abort_msg)
  return False


# Check if experiment data directory with same name exists
def check_for_data_locally(config):
  """Checks if experiment data already exists locally."""
  exp_data_path = "%s/data/%s" % (config.root_path, config.experiment_name)
  abort_str = "ABORT: re-run with different experiment name."
  if glob.glob(exp_data_path):
    if config.args.fail_silently:
      return True
    elif config.args.no:
      _abort(abort_str)
    elif config.args.yes:
      shutil.rmtree(exp_data_path)
    else:
      ovw = input(yellow("WARNING: experiment data exists. Overwrite? [Yn]"))
      if ovw in {"yes", "y", "Y", "YES", "Yes", ""}:
        shutil.rmtree(exp_data_path)
      else:
        _abort(abort_str)
  return False


def delete_data_in_gcs(config):
  """Deletes data in the configured GCS bucket for a fuzzing session."""
  sub_cmd = [
      "gsutil", "rm",
      "gs://%s-%s/%s/**" %
      (config.gcp_params["project_id"], config.gcp_params["data_bucket"],
       config.experiment_name)
  ]
  error_str = "ERROR: deleting existing data. Terminating Experiment!"
  run_cmd(sub_cmd, error_str)


def check_for_data_in_gcs(config):
  """Check Google Cloud Storage for existing experiment data files."""
  cmd = [
      "gsutil", "-q", "stat",
      "gs://%s-%s/%s/**" %
      (config.gcp_params["project_id"], config.gcp_params["data_bucket"],
       config.experiment_name)
  ]
  try:
    subprocess.check_call(cmd)
  except subprocess.CalledProcessError:
    return
  action_msg = "WARNING: experiment data exists in GCS. Overwrite? [Yn]"
  abort_msg = "ABORT: re-run with different experiment name."
  return _verify_action(config, delete_data_in_gcs, action_msg, abort_msg)


def delete_gce_vm(config):
  """Delete active Google Compute Engine VM running the same experiment."""
  cmd = ["gcloud", "compute", "instances", "delete", config.experiment_name]
  error_str = "ERROR: cannot delete GCE VM (%s). Aborting!" % (
      config.experiment_name)
  run_cmd(cmd, error_str)


def check_if_gce_vm_up(config):
  """Check if Google Compute Engine VM is running this experiment already."""
  cmd = ["gcloud", "compute", "instances", "list"]
  proc = subprocess.Popen(cmd,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          close_fds=True)
  while True:
    line = proc.stdout.readline()
    if not line:
      break
    line = line.decode("utf-8").rstrip("/\n")
    if config.experiment_name in line:
      action_msg = "WARNING: experiment already running on GCE. Overwrite? [Yn]"
      abort_msg = "ABORT: re-run with different experiment name."
      return _verify_action(config, delete_gce_vm, action_msg, abort_msg)


def build_docker_image(config):
  """Creates docker image containing DUT to fuzz."""
  print(LINE_SEP)
  print("Building Docker image to fuzz %s ..." % config.toplevel)
  print(LINE_SEP)
  cmd = [
      "docker", "build", "--build-arg",
      "FUZZER=%s" % config.fuzzer, "--build-arg",
      "VERSION=%s" % config.version, "-t", config.docker_image,
      "%s/hw/%s" % (config.root_path, config.toplevel)
  ]
  error_str = "ERROR: image build FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(green("IMAGE BUILD SUCCESSFUL -- Done!"))


# Create experiment data directories and copy over configs
def create_local_experiment_data_dir(config):
  """Creates local directories to store fuzzing experiment data."""
  print(LINE_SEP)
  print("Creating local directories for fuzzing data ...")
  print(LINE_SEP)
  exp_data_path = "%s/data/%s" % \
      (config.root_path, config.experiment_name)

  # Create directories
  os.makedirs(exp_data_path)
  os.chmod(exp_data_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
  os.mkdir(os.path.join(exp_data_path, "out"))
  os.chmod(os.path.join(exp_data_path, "out"),
           stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
  os.mkdir(os.path.join(exp_data_path, "logs"))
  os.chmod(os.path.join(exp_data_path, "logs"),
           stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

  # Copy over seeds that were used in this experiment
  seeds_dir = "%s/hw/%s/seeds" % (config.root_path, config.toplevel)
  seed_descripts_dir = "%s/hw/%s/seed_descriptions" % (config.root_path,
                                                       config.toplevel)
  if os.path.isdir(seeds_dir):
    shutil.copytree(seeds_dir, os.path.join(exp_data_path, "seeds"))
    os.chmod(os.path.join(exp_data_path, "seeds"),
             stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
  elif os.path.isdir(seed_descripts_dir):
    shutil.copytree(seed_descripts_dir,
                    os.path.join(exp_data_path, "seed_descriptions"))
    os.chmod(os.path.join(exp_data_path, "seed_descriptions"),
             stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
  else:
    print(red("ERROR: no seeds found. Terminating experiment!"))

  # Copy over HJSON config file that was used
  shutil.copy2(config.config_filename, exp_data_path)
  print(green("DIRECTORY CREATION SUCCESSFUL -- Done!"))
  return exp_data_path


def run_docker_container_locally(config, exp_data_path):
  """Runs a Docker container to fuzz the DUT on the local machine."""
  print(LINE_SEP)
  print("Running Docker container to fuzz %s ..." % config.toplevel)
  print(LINE_SEP)
  cmd = ["docker", "run", "-it", "--rm", "--name", config.experiment_name]
  # Set environment variables for general configs
  cmd.extend(["-e", "%s=%s" % ("TOPLEVEL", config.toplevel)])
  cmd.extend(["-e", "%s=%s" % ("VERSION", config.version)])
  cmd.extend(["-e", "%s=%s" % ("TB_TYPE", config.tb_type)])
  cmd.extend(["-e", "%s=%s" % ("TB", config.tb)])
  cmd.extend(["-e", "%s=%s" % ("FUZZER", config.fuzzer)])
  cmd.extend(["-e", "%s=%s" % ("INSTRUMENT_DUT", config.instrument_dut)])
  cmd.extend(["-e", "%s=%s" % ("INSTRUMENT_TB", config.instrument_tb)])
  cmd.extend(["-e", "%s=%s" % ("INSTRUMENT_VLTRT", config.instrument_vltrt)])
  cmd.extend(["-e", "%s=%s" % ("RUN_ON_GCP", config.run_on_gcp)])
  # Set environment variables for Verilator/HDL-generator/fuzzer params
  for params in config.env_var_params:
    for param, value in params.items():
      if value is not None:
        cmd.extend(["-e", "%s=%s" % (param.upper(), value)])
  # Mount volumes for output data
  cmd.extend(
      ["-v",
       "%s/logs:/src/hw/%s/logs" % (exp_data_path, config.toplevel)])
  cmd.extend(
      ["-v", "%s/out:/src/hw/%s/out" % (exp_data_path, config.toplevel)])
  # If manual mode, mount src code for development/debugging
  if config.manual:
    cmd.extend(
        ["-v", "%s/%s:/src/hw/seeder" % (config.root_path, SEEDER_PATH)])
    cmd.extend(["-v", "%s/%s:/src/hw/tb" % (config.root_path, SHARED_TB_PATH)])
    cmd.extend([
        "-v",
        "%s/hw/%s:/src/hw/%s" %
        (config.root_path, config.toplevel, config.toplevel)
    ])
    cmd.extend([
        "-v",
        "%s/infra/base-sim/common.mk:/src/hw/common.mk" % config.root_path
    ])
    cmd.extend(
        ["-v",
         "%s/infra/base-sim/exe.mk:/src/hw/exe.mk" % config.root_path])
  # Set target Docker image and run
  cmd.extend(["-t", config.docker_image])
  # If manual mode, start shell
  if config.manual:
    cmd.append("/bin/bash")
  error_str = "ERROR: container run FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(green("CONTAINER RUN SUCCESSFUL -- Done!"))


def check_if_docker_image_exists_in_gcr(config):
  """Checks if docker image exists in GCR already."""
  print(LINE_SEP)
  print("Checking if Docker image exists in GCR already ...")
  print(LINE_SEP)
  cmd = [
      "gcloud", "container", "images", "list",
      "--repository=gcr.io/%s" % config.gcp_params["project"]
  ]
  proc = subprocess.Popen(cmd,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          close_fds=True)
  line = proc.stdout.readline()  # first line is a header
  while True:
    line = proc.stdout.readline().decode("utf-8").rstrip()
    if not line:
      break
    if line == config.docker_image:
      return True
  return False


def push_docker_image_to_gcr(config):
  """Pushes docker image to GCR if it does not exist there yet."""
  print(LINE_SEP)
  print("Pushing Docker image to GCR ...")
  print(LINE_SEP)
  if config.args.update or not check_if_docker_image_exists_in_gcr(config):
    cmd = ["docker", "push", config.docker_image]
    error_str = "ERROR: pushing image to GCR FAILED. Terminating experiment!"
    run_cmd(cmd, error_str)
    print(green("IMAGE PUSH SUCCESSFUL -- Done!"))
  else:
    print(yellow("IMAGE ALREADY EXISTS IN GCR -- Done!"))


def push_vm_management_scripts_to_gcs(config):
  """Pushes VM management (startup/shutdown scripts to GCS."""
  print(LINE_SEP)
  print("Copying VM management script to GCS ...")
  print(LINE_SEP)
  cmd = [
      "gsutil", "cp",
      "%s/infra/hwfp/%s" %
      (config.root_path, config.gcp_params["startup_script"]),
      "gs://%s-%s/%s" % (config.gcp_params["project_id"],
                         config.gcp_params["vm_management_bucket"],
                         config.gcp_params["startup_script"])
  ]
  error_str = "ERROR: pushing scripts to GCS FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(green("COPY SUCCESSFUL -- Done!"))


def check_num_active_vm_instances(config):
  """Checks number of active VM instances on GCE as a $$$ safety measure."""
  print(LINE_SEP)
  print("Checking number of active VMs on GCE ...")
  print(LINE_SEP)
  cmd = [
      "gcloud", "compute", "instances", "list",
      "--zones=%s" % config.gcp_params["zone"]
  ]
  proc = subprocess.Popen(cmd,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          close_fds=True)
  num_active_vm_instances = -1  # first line is header
  while True:
    line = proc.stdout.readline()
    if not line:
      break
    num_active_vm_instances += 1
  if num_active_vm_instances < MAX_NUM_VM_INSTANCES:
    print(green("%d active VM(s)" % num_active_vm_instances))
  else:
    print(red("%d active VM(s)" % num_active_vm_instances))
    print(
        yellow("waiting %d seconds and trying again ..." %
               VM_LAUNCH_WAIT_TIME_S))
  return num_active_vm_instances


def run_docker_container_on_gce(config):
  """Runs a Docker container to fuzz the DUT on a Google Compute Engine VM."""
  # ***IMPORTANT: check how many VM instances currently up before launching***
  launch_vm = False
  while not launch_vm:
    # if above under $$$ threshold, create VM instance, else wait
    if check_num_active_vm_instances(config) < MAX_NUM_VM_INSTANCES:
      launch_vm = True
    else:
      time.sleep(VM_LAUNCH_WAIT_TIME_S)  # wait 10 seconds before trying again

  # Launch fuzzing container on VM
  print(LINE_SEP)
  print("Launching GCE VM to fuzz %s ..." % config.toplevel)
  print(LINE_SEP)
  cmd = [
      "gcloud", "compute",
      "--project=%s" % config.gcp_params["project_id"], "instances",
      "create-with-container", config.experiment_name, "--container-image",
      config.docker_image, "--container-stdin", "--container-tty",
      "--container-restart-policy",
      config.gcp_params["container_restart_policy"],
      "--zone=%s" % config.gcp_params["zone"],
      "--machine-type=%s" % config.gcp_params["machine_type"],
      "--boot-disk-size=%s" % config.gcp_params["boot_disk_size"],
      "--scopes=%s" % config.gcp_params["scopes"],
      "--metadata=startup-script-url=gs://%s-%s/%s" %
      (config.gcp_params["project_id"],
       config.gcp_params["vm_management_bucket"],
       config.gcp_params["startup_script"])
  ]
  # Open shell debugging
  if config.manual:
    cmd.append("--container-command=/bin/bash")
  # Set environment variables for general configs
  cmd.extend(["--container-env", "%s=%s" % ("TOPLEVEL", config.toplevel)])
  cmd.extend(["--container-env", "%s=%s" % ("VERSION", config.version)])
  cmd.extend(["--container-env", "%s=%s" % ("TB_TYPE", config.tb_type)])
  cmd.extend(["--container-env", "%s=%s" % ("TB", config.tb)])
  cmd.extend(["--container-env", "%s=%s" % ("FUZZER", config.fuzzer)])
  cmd.extend(
      ["--container-env",
       "%s=%s" % ("INSTRUMENT_DUT", config.instrument_dut)])
  cmd.extend(
      ["--container-env",
       "%s=%s" % ("INSTRUMENT_TB", config.instrument_tb)])
  cmd.extend([
      "--container-env",
      "%s=%s" % ("INSTRUMENT_VLTRT", config.instrument_vltrt)
  ])
  cmd.extend(["--container-env", "%s=%s" % ("RUN_ON_GCP", config.run_on_gcp)])
  # Set environment variables for Verilator/HDL-generator/fuzzer params
  for params in config.env_var_params:
    for param, value in params.items():
      if value is not None:
        cmd.extend(["--container-env", "%s=%s" % (param.upper(), value)])
  # launch container in VM instance
  error_str = "ERROR: launching VM on GCE FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(green("VM LAUNCH SUCCESSFUL -- Done!"))


# Main entry point
def fuzz(argv):
  """Runs fuzzing experiment with provided configuration filename."""
  # Parse cmd args
  module_description = "Hardware Fuzzing Pipeline"
  parser = argparse.ArgumentParser(description=module_description)
  parser.add_argument("-s",
                      "--fail-silently",
                      action="store_true",
                      help="Fail silently if data/VM already exists.")
  parser.add_argument("-n",
                      "--no",
                      action="store_true",
                      help="No to all prompts. (overides -y)")
  parser.add_argument("-y",
                      "--yes",
                      action="store_true",
                      help="Yes to all prompts.")
  parser.add_argument("-u",
                      "--update",
                      action="store_true",
                      help="Update Docker image in GCR.")
  parser.add_argument("config_filename",
                      metavar="config.hjson",
                      help="Configuration file in the HJSON format.")
  args = parser.parse_args(argv)

  # Load experiment configurations
  config = Config(args)

  # Check if experiment data already exists
  if config.run_on_gcp == 0:
    if check_for_data_locally(config):
      print(yellow("WARNING: experiment data exists locally... skipping."))
      return
  else:
    if check_for_data_in_gcs(config):
      print(yellow("WARNING: experiment data exists in GCS... skipping."))
      return
    if check_if_gce_vm_up(config):
      print(yellow("WARNING: experiment VM is already running... skipping."))
      return

  # Build docker image to fuzz target toplevel
  build_docker_image(config)

  # Run Docker container to fuzz toplevel
  if config.run_on_gcp == 0:
    exp_data_path = create_local_experiment_data_dir(config)
    run_docker_container_locally(config, exp_data_path)
  else:
    push_docker_image_to_gcr(config)
    push_vm_management_scripts_to_gcs(config)
    run_docker_container_on_gce(config)


if __name__ == "__main__":
  signal.signal(signal.SIGINT, _sigint_handler)
  fuzz(sys.argv[1:])
