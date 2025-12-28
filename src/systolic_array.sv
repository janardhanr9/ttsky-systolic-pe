module systolic_array(
    input logic [3:0] data_in,
    output logic [7:0] final_acc_out,
    input logic clk,
    input logic rst_n,
    input logic [3:0] weight_in,
    input logic [3:0] bias_in,
    input logic [3:0] pe_acc_en,   
    input logic [3:0] pe_weight_en,
    input logic [3:0] pe_bias_en,    
    input logic [1:0] drain_sel
);

logic [3:0] data_chain [0:3];
logic [7:0] acc_chain [0:3];

generate 
    genvar i;
    for (i = 0; i < 4; i = i + 1) begin : pe_chain
        systolic_pe pe_inst (
            .data_in      (i == 0 ? data_in : data_chain[i-1]),
            .data_out     (data_chain[i]),
            .clk          (clk),
            .rst_n        (rst_n),
            .weight_in    (weight_in),
            .bias_in      (bias_in),
            .acc_out      (acc_chain[i]),
            .acc_w_en     (pe_acc_en[i]),
            .weight_en    (pe_weight_en[i]),
            .bias_en      (pe_bias_en[i])
        );
    end
endgenerate

always_comb begin
        // Default assignment to avoid any potential latch inference
        final_acc_out = 8'b0;
        case (drain_sel)
            2'b00: final_acc_out = acc_chain[0];
            2'b01: final_acc_out = acc_chain[1];
            2'b10: final_acc_out = acc_chain[2];
            2'b11: final_acc_out = acc_chain[3];
            default: final_acc_out = 8'b0;
        endcase
    end

endmodule