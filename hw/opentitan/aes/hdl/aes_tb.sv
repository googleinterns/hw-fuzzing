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

module aes_tb
  import aes_reg_pkg::*;
(
  input clk_i,
  input rst_ni,

  output logic idle_o,

  input  tlul_pkg::tl_h2d_t tl_i,
  output tlul_pkg::tl_d2h_t tl_o,

  input  prim_alert_pkg::alert_rx_t [NumAlerts-1:0] alert_rx_i,
  output prim_alert_pkg::alert_tx_t [NumAlerts-1:0] alert_tx_o
);

  ////////////////
  //    DUT     //
  ////////////////
  aes dut (
    .clk_i,
    .rst_ni,

    .idle_o,

    .tl_i,
    .tl_o,

    .alert_rx_i,
    .alert_tx_o
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

  ////////////////
  // Assertions //
  ////////////////

endmodule
