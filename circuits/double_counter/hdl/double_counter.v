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

module double_counter(clk, n_reset, select, count_1, count_2);
    input            clk, n_reset, select;
    output reg [7:0] count_1, count_2;

    always @(posedge clk)
    begin
        if (~n_reset) begin
            count_1 <= 8'h00;
            count_2 <= 8'h00;
        end else begin
            if (select) begin
                count_1 <= count_1 + 1;
            end else begin
                count_2 <= count_2 + 1;
            end
        end
    end
endmodule
