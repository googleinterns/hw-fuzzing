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

CONFIG_DICT = {
    "experiment_name": "not-set",
    "toplevel": "not-set",
    "soc": "rfuzz",
    "version": "HEAD",
    "tb_type": "cpp",
    "tb": "afl",
    "fuzzer": "afl",
    "instrument_dut": 1,
    "instrument_tb": 0,
    "instrument_vltrt": 0,
    "manual": 0,
    "run_on_gcp": 1,
    "hdl_gen_params": {},
    "model_params": {},
    "fuzzer_params": {
        "interactive_mode": 1,
        "timeout_ms": None,
        "memory_limit_mb": None,
        "num_instances": 1,
        "mode": "m",
        "duration_mins": 1440,
    },
}
