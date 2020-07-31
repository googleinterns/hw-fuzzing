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

# Standard modules
import glob
import os
import shutil
import signal
import stat
import subprocess
import sys
import time

# Custom modules
from config import color_str_green
from config import color_str_red
from config import color_str_yellow
from config import Config

# Macros
NUM_ARGS = 1
LINE_SEP = "==================================================================="
MAX_NUM_VM_INSTANCES = 50
VM_LAUNCH_WAIT_TIME_S = 30


# Handler to gracefully exit on ctrl+c
def sigint_handler():
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
  exp_data_path = "%s/experiments/data/%s" % \
      (config.root_path, config.experiment_name)
  if glob.glob(exp_data_path):
    ovw = input(color_str_yellow( \
        "WARNING: experiment data exists. Overwrite? [Yn]"))
    if ovw in {"yes", "y", "Y", "YES", "Yes", ""}:
      shutil.rmtree(exp_data_path)
    else:
      abort_str = "ABORT: re-run with different experiment name."
      print(color_str_red(abort_str))
      sys.exit(1)


def check_for_data_in_gcs(config):
  """Check Google Cloud Storage for existing experiment data files."""
  cmd = ["gsutil", "-q", "stat", "gs://%s/%s/**" % \
      ("fuzzing-data", config.experiment_name)]
  try:
    subprocess.check_call(cmd)
  except subprocess.CalledProcessError:
    return
  ovw = input(color_str_yellow( \
      "WARNING: experiment data exists in GCS. Overwrite? [Yn]"))
  if ovw in {"yes", "y", "Y", "YES", "Yes", ""}:
    sub_cmd = ["gsutil", "rm", "gs://%s/%s/**" % \
        ("fuzzing-data", config.experiment_name)]
    error_str = "ERROR: deleting existing data. Terminating Experiment!"
    run_cmd(sub_cmd, error_str)
  else:
    abort_str = "ABORT: re-run with different experiment name."
    print(color_str_red(abort_str))
    sys.exit(1)


def build_docker_image(config):
  print(LINE_SEP)
  print("Building Docker image to fuzz %s ..." % config.circuit)
  print(LINE_SEP)
  cmd = ["docker", "build", \
      "-t", "gcr.io/hardware-fuzzing/%s" % config.circuit, \
      "%s/circuits/%s" % (config.root_path, config.circuit)]
  error_str = "ERROR: image build FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(color_str_green("IMAGE BUILD SUCCESSFUL -- Done!"))


# Create experiment data directories and copy over configs
def create_local_experiment_data_dir(config):
  """Creates local directories to store fuzzing experiment data."""
  print(LINE_SEP)
  print("Creating local directories for fuzzing data ...")
  print(LINE_SEP)
  exp_data_path = "%s/experiments/data/%s" % \
      (config.root_path, config.experiment_name)

  # Create directories
  os.mkdir(exp_data_path)
  os.chmod(exp_data_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
  os.mkdir(os.path.join(exp_data_path, "out"))
  os.chmod(os.path.join(exp_data_path, "out"), \
      stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
  os.mkdir(os.path.join(exp_data_path, "logs"))
  os.chmod(os.path.join(exp_data_path, "logs"), \
      stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

  # Copy over seeds that were used in this experiment
  seeds_dir = "%s/circuits/%s/seeds" % (config.root_path, config.circuit)
  shutil.copytree(seeds_dir, os.path.join(exp_data_path, "seeds"))
  os.chmod(os.path.join(exp_data_path, "seeds"), \
      stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

  # Copy over HJSON config file that was used
  shutil.copy2(config.config_filename, exp_data_path)
  print(color_str_green("DIRECTORY CREATION SUCCESSFUL -- Done!"))
  return exp_data_path


def run_docker_container_locally(config, exp_data_path):
  """Runs a Docker container to fuzz the DUT on the local machine."""
  print(LINE_SEP)
  print("Running Docker container to fuzz %s ..." % config.circuit)
  print(LINE_SEP)
  cmd = ["docker", "run", "-it", "--rm", "--name", config.experiment_name]
  # Set environment variables for general configs
  cmd.extend(["-e", "%s=%s" % ("CIRCUIT", config.circuit)])
  cmd.extend(["-e", "%s=%s" % ("TB", config.testbench)])
  cmd.extend(["-e", "%s=%s" % ("FUZZER", config.fuzzer)])
  cmd.extend(["-e", "%s=%s" % ("RUN_ON_GCP", config.run_on_gcp)])
  # Set environment variables for HDL generator configs
  for param, value in config.hdl_gen_params.items():
    if value is not None:
      cmd.extend(["-e", "%s=%s" % (param.upper(), value)])
  # Set environment variables for fuzzer configs
  for param, value in config.fuzzer_params.items():
    if value is not None:
      cmd.extend(["-e", "%s=%s" % (param.upper(), value)])
  # Mount volumes for output data
  cmd.extend(["-v", "%s/logs:/src/circuits/%s/logs" % \
      (exp_data_path, config.circuit)])
  cmd.extend(["-v", "%s/out:/src/circuits/%s/out" % \
      (exp_data_path, config.circuit)])
  # Set target Docker image and run
  cmd.extend(["-t", "gcr.io/hardware-fuzzing/%s" % config.circuit])
  # cmd.append("bash")
  error_str = "ERROR: container run FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(color_str_green("CONTAINER RUN SUCCESSFUL -- Done!"))


def push_docker_container_to_gcr(config):
  print(LINE_SEP)
  print("Pushing Docker image to GCR ...")
  print(LINE_SEP)
  cmd = ["docker", "push", "gcr.io/hardware-fuzzing/%s" % config.circuit]
  error_str = "ERROR: pushing image to GCR FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(color_str_green("IMAGE PUSH SUCCESSFUL -- Done!"))


def push_vm_management_scripts_to_gcs(config):
  print(LINE_SEP)
  print("Copying VM management script to GCS ...")
  print(LINE_SEP)
  cmd = ["gsutil", "cp", "%s/experiments/scripts/gce_vm_startup.sh" % \
      config.root_path, "gs://%s/gce_vm_startup.sh" % "vm-management"]
  error_str = "ERROR: pushing scripts to GCS FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(color_str_green("COPY SUCCESSFUL -- Done!"))


def check_num_active_vm_instances():
  """Checks number of active VM instances on GCE as a $$$ safety measure."""
  print(LINE_SEP)
  print("Checking number of active VMs on GCE ...")
  print(LINE_SEP)
  cmd = ["gcloud", "compute", "instances", "list"]
  proc = subprocess.Popen(\
      cmd, \
      stdin=subprocess.PIPE, \
      stdout=subprocess.PIPE, \
      stderr=subprocess.STDOUT, \
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
    print(color_str_yellow("waiting %d seconds and trying again ..." % \
        VM_LAUNCH_WAIT_TIME_S))
  return num_active_vm_instances


def run_docker_container_on_gce(config):
  """Runs a Docker container to fuzz the DUT on a Google Compute Engine VM."""

  # ***IMPORTANT: check how many VM instances currently up before launching***
  launch_vm = False
  while not launch_vm:
    # if above under $$$ threshold, create VM instance, else wait
    if check_num_active_vm_instances() < MAX_NUM_VM_INSTANCES:
      launch_vm = True
    else:
      time.sleep(VM_LAUNCH_WAIT_TIME_S)  # wait 10 seconds before trying again

  # Launch fuzzing container on VM
  print(LINE_SEP)
  print("Launching GCE VM to fuzz %s ..." % config.circuit)
  print(LINE_SEP)
  cmd = ["gcloud", "compute", "--project=%s" % "hardware-fuzzing", \
      "instances", "create-with-container", \
      config.experiment_name, "--container-image", \
      "gcr.io/%s/%s" % ("hardware-fuzzing", config.circuit),\
      "--container-restart-policy", "never", \
      "--zone=%s" % "us-east4-a", \
      "--machine-type=%s" % "n1-standard-1", \
      "--boot-disk-size=%s" % "10GB", \
      "--scopes=default,compute-rw,storage-rw", \
      "--metadata=startup-script-url=%s" % \
      "gs://vm-management/gce_vm_startup.sh"]
  # cmd.extend["--container-tty", "--container-stdin", "--container-arg=bash"]
  # Set environment variables for general configs
  cmd.extend(["--container-env", "%s=%s" % ("CIRCUIT", config.circuit)])
  cmd.extend(["--container-env", "%s=%s" % ("TB", config.testbench)])
  cmd.extend(["--container-env", "%s=%s" % ("FUZZER", config.fuzzer)])
  cmd.extend(["--container-env", "%s=%s" % ("RUN_ON_GCP", config.run_on_gcp)])
  # Set environment variables for HDL generator configs
  for param, value in config.hdl_gen_params.items():
    if value is not None:
      cmd.extend(["--container-env", "%s=%s" % (param.upper(), value)])
  # Set environment variables for fuzzer configs
  for param, value in config.fuzzer_params.items():
    if value is not None:
      cmd.extend(["--container-env", "%s=%s" % (param.upper(), value)])
  # launch container in VM instance
  error_str = "ERROR: launching VM on GCE FAILED. Terminating experiment!"
  run_cmd(cmd, error_str)
  print(color_str_green("VM LAUNCH SUCCESSFUL -- Done!"))


# Main entry point
def run_experiment(args):
  """Runs fuzzing experiment with provided configuration filename."""

  # Parse cmd args
  if len(args) != NUM_ARGS:
    print("Usage: [python3] ./run_experiment.py <config filename>")
    sys.exit(1)

  # Load experiment configurations
  config = Config(args[0])

  # Check if experiment data already exists
  if config.run_on_gcp == 0:
    check_for_data_locally(config)
  else:
    check_for_data_in_gcs(config)

  # Build docker image to fuzz target circuit
  build_docker_image(config)

  # Run Docker container to fuzz circuit
  if config.run_on_gcp == 0:
    exp_data_path = create_local_experiment_data_dir(config)
    run_docker_container_locally(config, exp_data_path)
  else:
    push_docker_container_to_gcr(config)
    push_vm_management_scripts_to_gcs(config)
    run_docker_container_on_gce(config)

if __name__ == "__main__":
  signal.signal(signal.SIGINT, sigint_handler)
  run_experiment(sys.argv[1:])
