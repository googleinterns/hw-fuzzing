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
"""This module contains methods to fuzz hw IP block in hw/.

Description:
This module contains several methods that:
1. Parses an HJSON configuration file defining which toplevel to fuzz and how to
   fuzz it (i.e. HDL-generation/testbench/GCP/Verilator/fuzzer parameters).
2. Builds a Docker image containing the DUT (toplevel) HDL, the desired
   testbench, fuzzer, Verilator (simulation engine), and compilation/simulation
   scripts).
3. Checks if a data already exists/Creates a directory to store the fuzzing
   results either locally or in a GCS bucket.
4. Launches a Docker container either locally or on a GCE VM to fuzz the DUT.

Usage Example:
  fuzz.py <HSJON configuration file>

For a reference on how to define the HJSON configuration files, see tests/.
"""

# Standard modules
import argparse
import glob
import os
import shutil
import signal
import stat
import subprocess
import sys
import time

# Custom modules
from config import Config, color_str_green, color_str_red, color_str_yellow

LINE_SEP = "==================================================================="
MAX_NUM_VM_INSTANCES = 36  # this is max default quota for us-east4-a zone
VM_LAUNCH_WAIT_TIME_S = 30


# Handler to gracefully exit on ctrl+c
def sigint_handler(sig, frame):
  print(color_str_red("\nTERMINATING EXPERIMENT!"))
  sys.exit(0)


# Run command as subprocess catching non-zero exit codes
def run_cmd(cmd, error_str):
  try:
    print("Running command:")
    print(color_str_yellow(subprocess.list2cmdline(cmd)))
    subprocess.check_call(cmd)
  except subprocess.CalledProcessError:
    print(color_str_red(error_str))
    sys.exit(1)


# Check if experiment data directory with same name exists
def check_for_data_locally(config):
  """Checks if experiment data already exists locally."""
  exp_data_path = "%s/data/%s" % (config.root_path, config.experiment_name)
  if glob.glob(exp_data_path):
    if config.args.yes:
      shutil.rmtree(exp_data_path)
    else:
      ovw = input(
          color_str_yellow("WARNING: experiment data exists. Overwrite? [Yn]"))
      if ovw in {"yes", "y", "Y", "YES", "Yes", ""}:
        shutil.rmtree(exp_data_path)
      else:
        abort_str = "ABORT: re-run with different experiment name."
        print(color_str_red(abort_str))
        sys.exit(1)


def delete_data_in_gcs(config):
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
  if config.args.yes:
    delete_data_in_gcs(config)
  else:
    ovw = input(
        color_str_yellow(
            "WARNING: experiment data exists in GCS. Overwrite? [Yn]"))
    if ovw in {"yes", "y", "Y", "YES", "Yes", ""}:
      delete_data_in_gcs(config)
    else:
      abort_str = "ABORT: re-run with different experiment name."
      print(color_str_red(abort_str))
      sys.exit(1)


def build_docker_image(config):
  """Creates docker image containing DUT to fuzz."""
  print(LINE_SEP)
  print("Building Docker image to fuzz %s ..." % config.toplevel)
  print(LINE_SEP)
  cmd = [
      "docker", "build", "--build-arg",
      "FUZZER=%s" % config.fuzzer, "-t", config.docker_image,
      "%s/hw/%s" % (config.root_path, config.toplevel)
  ]
  error_str = "ERROR: image build FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(color_str_green("IMAGE BUILD SUCCESSFUL -- Done!"))


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
  shutil.copytree(seeds_dir, os.path.join(exp_data_path, "seeds"))
  os.chmod(os.path.join(exp_data_path, "seeds"),
           stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

  # Copy over HJSON config file that was used
  shutil.copy2(config.config_filename, exp_data_path)
  print(color_str_green("DIRECTORY CREATION SUCCESSFUL -- Done!"))
  return exp_data_path


def run_docker_container_locally(config, exp_data_path):
  """Runs a Docker container to fuzz the DUT on the local machine."""
  print(LINE_SEP)
  print("Running Docker container to fuzz %s ..." % config.toplevel)
  print(LINE_SEP)
  cmd = ["docker", "run", "-it", "--rm", "--name", config.experiment_name]
  # Set environment variables for general configs
  cmd.extend(["-e", "%s=%s" % ("TOPLEVEL", config.toplevel)])
  cmd.extend(["-e", "%s=%s" % ("TB_TYPE", config.tb_type)])
  cmd.extend(["-e", "%s=%s" % ("TB", config.tb)])
  cmd.extend(["-e", "%s=%s" % ("FUZZER", config.fuzzer)])
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
  # Set target Docker image and run
  cmd.extend(["-t", config.docker_image])
  # TODO(ttrippel): add debug flag to launch container in interactively w/ shell
  # cmd.append("bash")
  error_str = "ERROR: container run FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(color_str_green("CONTAINER RUN SUCCESSFUL -- Done!"))


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
    print(color_str_green("IMAGE PUSH SUCCESSFUL -- Done!"))
  else:
    print(color_str_yellow("IMAGE ALREADY EXISTS IN GCR -- Done!"))


def push_vm_management_scripts_to_gcs(config):
  print(LINE_SEP)
  print("Copying VM management script to GCS ...")
  print(LINE_SEP)
  cmd = [
      "gsutil", "cp",
      "%s/infra/gcp/%s" % (config.root_path, config.gcp_params),
      "gs://%s-%s/%s" % (config.gcp_params["project_id"],
                         config.gcp_params["vm_management_bucket"],
                         config.gcp_params["startup_script"])
  ]
  error_str = "ERROR: pushing scripts to GCS FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(color_str_green("COPY SUCCESSFUL -- Done!"))


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
    print(color_str_green("%d active VM(s)" % num_active_vm_instances))
  else:
    print(color_str_red("%d active VM(s)" % num_active_vm_instances))
    print(
        color_str_yellow("waiting %d seconds and trying again ..." %
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
      "--project=%s" % config.gcp_params["project"], "instances",
      "create-with-container", config.experiment_name, "--container-image",
      config.docker_image, "--container-restart-policy",
      config.gcp_params["container_restart_policy"],
      "--zone=%s" % config.gcp_params["zone"],
      "--machine-type=%s" % config.gcp_params["machine_type"],
      "--boot-disk-size=%s" % config.gcp_params["boot_disk_size"],
      "--scopes=%s" % config.gcp_params["scopes"],
      "--metadata=startup-script-url=%s" %
      config.gcp_params["startup_script_url"]
  ]
  # TODO(ttrippel): add debug flag to launch container interactively w/ shell
  # cmd.extend["--container-tty", "--container-stdin", "--container-arg=bash"]
  # Set environment variables for general configs
  cmd.extend(["--container-env", "%s=%s" % ("TOPLEVEL", config.toplevel)])
  cmd.extend(["--container-env", "%s=%s" % ("TB_TYPE", config.tb_type)])
  cmd.extend(["--container-env", "%s=%s" % ("TB", config.tb)])
  cmd.extend(["--container-env", "%s=%s" % ("FUZZER", config.fuzzer)])
  cmd.extend(["--container-env", "%s=%s" % ("RUN_ON_GCP", config.run_on_gcp)])
  # Set environment variables for Verilator/HDL-generator/fuzzer params
  for params in config.env_var_params:
    for param, value in params.items():
      if value is not None:
        cmd.extend(["--container-env", "%s=%s" % (param.upper(), value)])
  # launch container in VM instance
  error_str = "ERROR: launching VM on GCE FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(color_str_green("VM LAUNCH SUCCESSFUL -- Done!"))


# Main entry point
def fuzz(argv):
  """Runs fuzzing experiment with provided configuration filename."""

  # Parse cmd args
  module_description = "Hardware Fuzzing Pipeline"
  parser = argparse.ArgumentParser(description=module_description)
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
    check_for_data_locally(config)
  else:
    check_for_data_in_gcs(config)

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
  signal.signal(signal.SIGINT, sigint_handler)
  fuzz(sys.argv[1:])
