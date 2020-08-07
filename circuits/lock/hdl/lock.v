module lock(
    input wire reset_n,
    input wire clk,

    input wire [3:0] code,
    output wire [1:0] state,
    output wire unlocked
    );

    reg [1:0] __reg_state_0;
    wire [1:0] __reg_state_0_next;

    always @(posedge clk, negedge reset_n) begin
        if (~reset_n) begin
            __reg_state_0 <= 2'h0;
        end
        else begin
            __reg_state_0 <= __reg_state_0_next;
        end
    end

    wire __temp_0;
    wire __temp_1;
    wire __temp_2;
    wire __temp_3;
    wire __temp_4;
    wire __temp_5;
    wire __temp_6;
    wire __temp_7;
    wire __temp_8;
    wire __temp_9;
    wire [1:0] __temp_10;
    wire [1:0] __temp_11;
    wire [1:0] __temp_12;

    assign state = __reg_state_0;
    assign __temp_0 = __reg_state_0 == 2'h3;
    assign unlocked = __temp_0;
    assign __temp_1 = __reg_state_0 == 2'h2;
    assign __temp_2 = code == 4'h3;
    assign __temp_3 = __temp_1 & __temp_2;
    assign __temp_4 = __reg_state_0 == 2'h1;
    assign __temp_5 = code == 4'h4;
    assign __temp_6 = __temp_4 & __temp_5;
    assign __temp_7 = __reg_state_0 == 2'h0;
    assign __temp_8 = code == 4'h6;
    assign __temp_9 = __temp_7 & __temp_8;
    assign __temp_10 = __temp_9 ? 2'h1 : __reg_state_0;
    assign __temp_11 = __temp_6 ? 2'h2 : __temp_10;
    assign __temp_12 = __temp_3 ? 2'h3 : __temp_11;
    assign __reg_state_0_next = __temp_12;

endmodule

