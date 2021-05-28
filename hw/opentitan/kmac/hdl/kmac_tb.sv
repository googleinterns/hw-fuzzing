// Copyright 2020 Timothy Trippel
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


`include "hwf_assert.sv"

module kmac_tb
  import kmac_pkg::*;
(
  input clk_i,
  input rst_ni,

  input clk_edn_i,
  input rst_edn_ni,

  input  tlul_pkg::tl_h2d_t tl_i,
  output tlul_pkg::tl_d2h_t tl_o,

  // KeyMgr sideload (secret key) interface
  input keymgr_pkg::hw_key_req_t keymgr_key_i,

  // KeyMgr KDF data path
  input  app_req_t [NumAppIntf-1:0] app_i,
  output app_rsp_t [NumAppIntf-1:0] app_o,

  // EDN interface
  output edn_pkg::edn_req_t entropy_o,
  input  edn_pkg::edn_rsp_t entropy_i,

  // interrupts
  output logic intr_kmac_done_o,
  output logic intr_fifo_empty_o,
  output logic intr_kmac_err_o,

  // Idle signal
  output logic idle_o
);

  //////////////////
  //     DUT      //
  //////////////////
  kmac dut (
    .clk_i,
    .rst_ni,

    .clk_edn_i,
    .rst_edn_ni,

    .tl_i,
    .tl_o,

    .keymgr_key_i,
    .app_i,
    .app_o,

    .intr_kmac_done_o,
    .intr_fifo_empty_o,
    .intr_kmac_err_o,
    
    .idle_o
  );

`ifdef UNPACK_TLUL
  //////////////////
  // Unpack TL-UL //
  //////////////////
  tlul_inspect inspect (
    .tl_i,
    .tl_o
  );
`endif

  //////////////////
  //  Assertions  //
  //////////////////
  `HWF_ASSERT(GitHubIssue6408, ((dut.kmac_st == 3) && dut.sha3_absorbed 
    && dut.sha3_done) |-> (dut.kmac_st_d == 0))

endmodule
