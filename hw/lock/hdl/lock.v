// Copyright 2020 Google LLC
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

module lock(
  input wire reset_n,
  input wire clk,
  input wire [7:0] code,
  output reg [1:0] state,
  output wire unlocked
);

assign unlocked = state == 2'b11 ? 1'b1 : 1'b0;

always @(posedge clk) begin
  if (~reset_n) begin
    state <= 2'b00;
  end
  else begin
    case(state)
      2'b00   : state <= code == 8'haa ? 2'b01 : 2'b00;
      2'b01   : state <= code == 8'hbb ? 2'b10 : 2'b01;
      2'b10   : state <= code == 8'hcc ? 2'b11 : 2'b10;
      default : state <= state;
    endcase
  end
end

endmodule
