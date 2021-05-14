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

module lock_tb(
  input wire reset_n,
  input wire clk,
  input wire  [3:0] code,
  output reg [3:0] state,
  output wire unlocked
);

  ////////////////
  //    DUT     //
  ////////////////
  lock dut (
    .reset_n,
    .clk,
    .code,
    .state,
    .unlocked
  );

  ////////////////
  // Assertions //
  ////////////////
  assert property (@(posedge clk) disable iff (reset_n === '0) !unlocked) else
  begin
      $error("SUCCESS: unlocked state has been reached.");
  end
endmodule


