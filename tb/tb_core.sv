`timescale 1ns/1ps
`include "../common_pkg.sv"
module tb_core;
  logic clk=0, rstn=0, start=0;
  wire finish;
  logic [NumOfCU-1:0] im_init_wr_en='0, sm1_init_wr_en='0, sm2_init_wr_en='0, dm_done_rd_en='0;
  logic [NumOfCU-1:0][g_R-1:0] im_init_wr_addr='0;
  logic [NumOfCU-1:0][g_Q-1:0] sm1_init_wr_addr='0;
  logic [NumOfCU-1:0][g_T-1:0] sm2_init_wr_addr='0,dm_done_rd_addr='0;
  logic [NumOfCU-1:0][INS_L-1:0] im_init_wr_data='0;
  logic [NumOfCU-1:0][WORD_LEN-1:0] sm1_init_wr_data='0, sm2_init_wr_data='0;
  wire [NumOfCU-1:0][WORD_LEN-1:0] dm_done_rd_data;
  logic [INS_L-1:0] im [0:NumOfCU*DEPTH_IM-1];
  logic [WORD_LEN-1:0] sm1 [0:NumOfCU*DEPTH_SM1-1];
  logic [WORD_LEN-1:0] sm2 [0:NumOfCU*DEPTH_SM2-1];
  string directory;
  integer count=0, fd;
  always #5 clk=~clk;
  stpu_top dut(.*);
  initial begin
    if (!$value$plusargs("directory=%s", directory)) $fatal(1,"missing directory");
    $readmemh({directory,"/im.hex"},im);
    $readmemh({directory,"/sm1.hex"},sm1);
    $readmemh({directory,"/sm2.hex"},sm2);
    repeat(4) @(negedge clk);
    rstn=1;
    // Exercise author memory ports; initialize all CUs in parallel.
    for(int a=0;a<DEPTH_IM;a++) begin
      @(negedge clk);
      im_init_wr_en='1; sm1_init_wr_en='1;
      sm2_init_wr_en=(a<DEPTH_SM2)?'1:'0;
      for(int u=0;u<NumOfCU;u++) begin
        im_init_wr_addr[u]=a; im_init_wr_data[u]=im[u*DEPTH_IM+a];
        sm1_init_wr_addr[u]=a;sm1_init_wr_data[u]=sm1[u*DEPTH_SM1+a];
        sm2_init_wr_addr[u]=a;
        if(a<DEPTH_SM2) sm2_init_wr_data[u]=sm2[u*DEPTH_SM2+a];
      end
    end
    @(negedge clk);
    im_init_wr_en='0;sm1_init_wr_en='0;sm2_init_wr_en='0;
    @(negedge clk);start=1;
    while(!finish && count<20000) begin
      @(posedge clk); #1; count=count+1;
    end
    if(!finish) $fatal(1,"whole solve timeout");
    $display("CORE_RTL_FINISH cycles=%0d",count);
    fd=$fopen({directory,"/dm.hex"},"w");
    if(!fd) $fatal(1,"output open failed");
    for(int a=0;a<DEPTH_DM;a++) begin
      @(negedge clk);dm_done_rd_en='1;
      for(int u=0;u<NumOfCU;u++) dm_done_rd_addr[u]=a;
      @(posedge clk); #1;
      for(int u=0;u<NumOfCU;u++) $fdisplay(fd,"%0d %0d %08x",u,a,dm_done_rd_data[u]);
    end
    $fclose(fd);$finish;
  end
endmodule
