module sync #(
	parameter integer n=1,
	parameter integer depth=2
) (
	input [n-1:0] in,
	output [n-1:0] out,
	input clk
);

	reg [n-1:0] hist [depth+1];

	assign hist[0] = in;
	assign out = hist[depth];

	genvar i;
	generate
		for (i=0; i<depth; i=i+1) begin
			always @(posedge clk) begin
				hist[i+1] <= hist[i];
			end
		end
	endgenerate

endmodule 

module reg_map(
	// generic interface
	input clk,
	input rst,
	input [7:0] i_addr,
	input [7:0] o_addr,
	input [31:0] i_data,
	output reg [31:0] o_data,
	// design-specific I/O
	input [5:0] a,
	input [6:0] b,
	output reg [7:0] c,
	output reg [8:0] d
);

    // Initial values for parameters
    wire [7:0] c_def;
    assign c_def = 0;
    
    wire [8:0] d_def;
    assign d_def = 0;
    
    

	// combo mux for reading outputs from design
	always @* begin
		case (o_addr)
			'd0: o_data = a;
			'd1: o_data = b;
			// ...
			default: o_data = a;
		endcase
	end

	// register map for writing to the inputs of the design
	always @(posedge clk) begin
		if (rst == 'b1) begin
			c <= c_def; // use VIO defaults
		end else if (i_addr == 'd0) begin 
			c <= i_data;
		end else begin
			c <= c;
		end
	end 

	always @(posedge clk) begin
		if (rst == 'b1) begin
			d <= d_def; // use VIO defaults
		end else if (i_addr == 'd1) begin 
			d <= i_data;
		end else begin
			d <= d;
		end
	end 

endmodule