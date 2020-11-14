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

module tlul_inspect (
  input tlul_pkg::tl_h2d_t tl_i,
  input tlul_pkg::tl_d2h_t tl_o
);

// Host-to-Device Signals
// A - Channel
logic                         a_valid;
logic                  [2:0]  a_opcode;
logic                  [2:0]  a_param;
logic  [top_pkg::TL_SZW-1:0]  a_size;
logic  [top_pkg::TL_AIW-1:0]  a_source;
logic   [top_pkg::TL_AW-1:0]  a_address;
logic  [top_pkg::TL_DBW-1:0]  a_mask;
logic   [top_pkg::TL_DW-1:0]  a_data;
logic                 [16:0]  a_user;
// D - Channel
logic                         d_ready;

// Device-to-Host Signals
// D - Channel
logic                         d_valid;
logic                  [2:0]  d_opcode;
logic                  [2:0]  d_param;
logic  [top_pkg::TL_SZW-1:0]  d_size;
logic  [top_pkg::TL_AIW-1:0]  d_source;
logic  [top_pkg::TL_DIW-1:0]  d_sink;
logic   [top_pkg::TL_DW-1:0]  d_data;
logic  [top_pkg::TL_DUW-1:0]  d_user;
logic                         d_error;
// A - Channel
logic                         a_ready;

// Host-to-Device Signals
// A - Channel
assign a_valid   = tl_i[101];
assign a_opcode  = tl_i[100:98];
assign a_param   = tl_i[97:95];
assign a_size    = tl_i[94:93];
assign a_source  = tl_i[92:85];
assign a_address = tl_i[84:53];
assign a_mask    = tl_i[52:49];
assign a_data    = tl_i[48:17];
assign a_user    = tl_i[16:1];
// D - Channel
assign d_ready = tl_i[0];

// Device-to-Host Signals
// D - Channel
assign d_valid   = tl_o[67];
assign d_opcode  = tl_o[66:64];
assign d_param   = tl_o[63:61];
assign d_size    = tl_o[60:59];
assign d_source  = tl_o[58:51];
assign d_sink  = tl_o[50];
assign d_data  = tl_o[49:18];
assign d_user  = tl_o[17:2];
assign d_error  = tl_o[1];
// A - Channel
assign a_ready  = tl_o[0];

endmodule

