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

// Modified OpenTitan macro bodies included by prim_assert.sv that are
// compatable with Verilator's partial support of SystemVerilog SVA syntax. See 
// prim_assert.sv for documentation for each of the macros.

// ASSERT_RPT is available to change the reporting mechanism when an assert fails
`define ASSERT_RPT(__name)                                                  \
  $error("[ASSERT FAILED] [%m] %s (%s:%0d)", __name, `__FILE__, `__LINE__); \

// Immediate assertions are currently, *NOT* supported by Verilator
`define ASSERT_I(__name, __prop)
`define ASSERT_INIT(__name, __prop)
`define ASSERT_FINAL(__name, __prop)

// A subset of the concurrent assertion syntax *IS* supported by verilator
`define ASSERT(__name, __prop, __clk = `ASSERT_DEFAULT_CLK, __rst = `ASSERT_DEFAULT_RST) \
  __name: assert property (@(posedge __clk) disable iff ((__rst) !== '0) __prop)         \
    else begin                                                                           \
      `ASSERT_RPT(`PRIM_STRINGIFY(__name))                                               \
    end

`define ASSERT_NEVER(__name, __prop, __clk = `ASSERT_DEFAULT_CLK, __rst = `ASSERT_DEFAULT_RST) \
  __name: assert property (@(posedge __clk) disable iff ((__rst) !== '0) not __prop)           \
    else begin                                                                                 \
      `ASSERT_RPT(`PRIM_STRINGIFY(__name))                                                     \
    end

`define ASSERT_KNOWN(__name, __sig, __clk = `ASSERT_DEFAULT_CLK, __rst = `ASSERT_DEFAULT_RST) \
  `ASSERT(__name, !$isunknown(__sig), __clk, __rst)

`define COVER(__name, __prop, __clk = `ASSERT_DEFAULT_CLK, __rst = `ASSERT_DEFAULT_RST) \
  __name: cover property (@(posedge __clk) disable iff ((__rst) !== '0) __prop);

`define ASSUME(__name, __prop, __clk = `ASSERT_DEFAULT_CLK, __rst = `ASSERT_DEFAULT_RST) \
  __name: assume property (@(posedge __clk) disable iff ((__rst) !== '0) __prop)         \
    else begin                                                                           \
      `ASSERT_RPT(`PRIM_STRINGIFY(__name))                                               \
    end

`define ASSUME_I(__name, __prop)           \
  __name: assume (__prop)                  \
    else begin                             \
      `ASSERT_RPT(`PRIM_STRINGIFY(__name)) \
    end

