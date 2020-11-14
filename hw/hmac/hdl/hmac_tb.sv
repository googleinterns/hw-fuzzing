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


`include "prim_assert.sv"

module hmac_tb (
  input clk_i,
  input rst_ni,

  input  tlul_pkg::tl_h2d_t tl_i,
  output tlul_pkg::tl_d2h_t tl_o,
  
  output logic intr_hmac_done_o,
  output logic intr_fifo_empty_o,
  output logic intr_hmac_err_o,

  output logic idle_o
);

  ////////////////
  //    DUT     //
  ////////////////
  hmac dut (
    .clk_i,
    .rst_ni,

    .tl_i,
    .tl_o,

    .intr_hmac_done_o,
    .intr_fifo_empty_o,
    .intr_hmac_err_o,

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

  ////////////////
  // Assertions //
  ////////////////

endmodule
