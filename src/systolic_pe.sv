module systolic_pe (
    input logic [7:0] data_in,
    output logic [7:0] data_out,
    input logic clk,
    input logic rst_n,
    input logic [7:0] weight_in,
    input logic [7:0] bias_in,
    output logic [15:0] acc_out,
    input logic acc_w_en,
    input logic weight_en,
    input logic bias_en
);

    logic signed [15:0] accumulator;
    logic signed [7:0] weight;
    logic signed [7:0] pass_through_data;

    assign acc_out = accumulator;
    assign data_out = pass_through_data;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin 
            accumulator <= 16'b0;
            weight <= 8'b0;
        end else begin
            pass_through_data <= data_in;
            // load
            if (weight_en) begin
                weight <= weight_in;
            end
            if (bias_en) begin
                accumulator <= {{8{bias_in[7]}}, bias_in}; // sign-extend 8-bit bias into 16-bit accumulator
            end
            if (acc_w_en) begin
                accumulator <= accumulator + (data_in * weight);
            end
        end
    end
endmodule