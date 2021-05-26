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

module rv_timer_tb (
  input clk_i,
  input rst_ni,

  input  tlul_pkg::tl_h2d_t tl_i,
  output tlul_pkg::tl_d2h_t tl_o,

  output logic intr_timer_expired_0_0_o
);

  ////////////////
  //    DUT     //
  ////////////////
  rv_timer dut (
    .clk_i,
    .rst_ni,

    .tl_i,
    .tl_o,

    .intr_timer_expired_0_0_o
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
`ifdef DEMO
  wire [63:0] timer_value;
  wire [63:0] compare_value;
  assign timer_value = {dut.u_reg.reg2hw.timer_v_upper0, dut.u_reg.reg2hw.timer_v_lower0};
  assign compare_value = {dut.u_reg.reg2hw.compare_upper0_0.q, dut.u_reg.reg2hw.compare_lower0_0.q};
  `HWF_ASSERT(IntrMissed, (dut.intr_timer_en && (timer_value >= compare_value))
    |-> dut.intr_timer_set);
`endif

endmodule
