// Copyright 2021 Timothy Trippel
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

`ifndef HWF_ASSERT_SV
`define HWF_ASSERT_SV

`include "prim_assert.sv"

// Modified OpenTitan macro bodies included by prim_assert.sv that are
// compatable with Verilator's partial support of SystemVerilog SVA syntax. See 
// prim_assert.sv for documentation for each of the macros.

// The list of basic macros supported is:
//
//  ASSERT:       Assert a concurrent property directly. It can be called as a 
//                module (or interface) body item.
//
//                Note: We use (__rst !== '0) in the disable iff statements 
//                instead of (__rst == '1). This properly disables the assertion
//                in cases when reset is X at the beginning of a simulation. For
//                that case, (reset == '1) does not disable the assertion.
//
//  ASSERT_NEVER: Assert a concurrent property NEVER happens
//
//  ASSERT_KNOWN: Assert that signal has a known value (each bit is either '0'
//                or '1') after reset. It can be called as a module (or
//                interface) body item.

// ASSERT_RPT is available to change the reported message when an assert fails
`define HWF_ASSERT_RPT(__name)                                              \
  $error("[ASSERT FAILED] [%m] %s (%s:%0d)", __name, `__FILE__, `__LINE__); \

// A subset of the concurrent assertion syntax *IS* supported by verilator
`define HWF_ASSERT(__name, __prop, __clk = `ASSERT_DEFAULT_CLK, __rst = `ASSERT_DEFAULT_RST) \
  __name: assert property (@(posedge __clk) disable iff ((__rst) !== '0) __prop)             \
    else begin                                                                               \
      `HWF_ASSERT_RPT(`PRIM_STRINGIFY(__name))                                               \
    end

`endif // HWF_ASSERT_SV
