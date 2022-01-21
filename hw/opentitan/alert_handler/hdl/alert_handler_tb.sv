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

module alert_handler_tb
  import alert_pkg::*;
  import prim_alert_pkg::*;
  import prim_esc_pkg::*;
(
  input clk_i,
  input rst_ni,
  
  input  tlul_pkg::tl_h2d_t tl_i,
  output tlul_pkg::tl_d2h_t tl_o,

  output logic intr_classa_o,
  output logic intr_classb_o,
  output logic intr_classc_o,
  output logic intr_classd_o,

  output alert_crashdump_t crashdump_o,

  input entropy_i,

  input  alert_tx_t [NAlerts-1:0] alert_tx_i,
  output alert_rx_t [NAlerts-1:0] alert_rx_o,

  input  esc_rx_t [N_ESC_SEV-1:0] esc_rx_i,
  output esc_tx_t [N_ESC_SEV-1:0] esc_tx_o
);

  ////////////////
  //    DUT     //
  ////////////////
  alert_handler dut (
    .clk_i,
    .rst_ni,

    .tl_i,
    .tl_o,

    .intr_classa_o,
    .intr_classb_o,
    .intr_classc_o,
    .intr_classd_o,

    .crashdump_o,

    .entropy_i,

    .alert_tx_i,
    .alert_rx_o,

    .esc_rx_i,
    .esc_tx_o
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
  //assert property (@(posedge clk_i) disable iff (rst_ni === '0) 
    //(dut.i_reg_wrap.u_reg.regen_qs == '0) |=> 
    //(dut.i_reg_wrap.u_reg.regen_qs == '0)) else
  //begin
      //$error("Alert Handler CSRs unlockable by software.");
  //end

endmodule
