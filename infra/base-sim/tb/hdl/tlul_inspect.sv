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

module tlul_inspect (
  input tlul_pkg::tl_h2d_t tl_i,
  input tlul_pkg::tl_d2h_t tl_o
);

// Host-to-Device Signals
// A - Channel
logic                         a_valid;
tlul_pkg::tl_a_op_e           a_opcode;
logic                  [2:0]  a_param;
logic  [top_pkg::TL_SZW-1:0]  a_size;
logic  [top_pkg::TL_AIW-1:0]  a_source;
logic   [top_pkg::TL_AW-1:0]  a_address;
logic  [top_pkg::TL_DBW-1:0]  a_mask;
logic   [top_pkg::TL_DW-1:0]  a_data;
tlul_pkg::tl_a_user_t         a_user;
// D - Channel
logic                         d_ready;

// Device-to-Host Signals
// D - Channel
logic                         d_valid;
tlul_pkg::tl_d_op_e           d_opcode;
logic                  [2:0]  d_param;
logic  [top_pkg::TL_SZW-1:0]  d_size;
logic  [top_pkg::TL_AIW-1:0]  d_source;
logic  [top_pkg::TL_DIW-1:0]  d_sink;
logic   [top_pkg::TL_DW-1:0]  d_data;
tlul_pkg::tl_d_user_t         d_user;
logic                         d_error;
// A - Channel
logic                         a_ready;

// Host-to-Device Signals
// A - Channel
assign 
{a_valid   ,
 a_opcode  ,
 a_param   ,
 a_size    ,
 a_source  ,
 a_address ,
 a_mask    ,
 a_data    ,
 a_user    ,
 d_ready} = tl_i;

// Device-to-Host Signals
// D - Channel
assign 
{d_valid  ,
 d_opcode ,
 d_param  ,
 d_size   ,
 d_source ,
 d_sink   ,
 d_data   ,
 d_user   ,
 d_error  ,
 a_ready} = tl_o;

endmodule

