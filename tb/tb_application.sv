`timescale 1ns/1ps
`include "../common_pkg.sv"
module tb_application;
  logic clk=0,rstn=0,start=0;
  wire finish;
  logic [NumOfCU-1:0] im_init_wr_en='0,sm1_init_wr_en='0,sm2_init_wr_en='0,dm_done_rd_en='0;
  logic [NumOfCU-1:0][g_R-1:0] im_init_wr_addr='0;
  logic [NumOfCU-1:0][g_Q-1:0] sm1_init_wr_addr='0;
  logic [NumOfCU-1:0][g_T-1:0] sm2_init_wr_addr='0,dm_done_rd_addr='0;
  logic [NumOfCU-1:0][INS_L-1:0] im_init_wr_data='0;
  logic [NumOfCU-1:0][WORD_LEN-1:0] sm1_init_wr_data='0,sm2_init_wr_data='0;
  wire [NumOfCU-1:0][WORD_LEN-1:0] dm_done_rd_data;
  logic [INS_L-1:0] im[0:NumOfCU*DEPTH_IM-1];
  logic [WORD_LEN-1:0] sm1[0:NumOfCU*DEPTH_SM1-1],sm2[0:NumOfCU*DEPTH_SM2-1];
  integer lengths[0:4*NumOfCU-1];
  string directory;
  integer ports=8,group_load,group_dm,qcount=3;
  integer tick=0,count=0,fd,max_load=0,max_dm=0,begin_tick,launch_tick,end_tick;
  always #5 clk=~clk;
  always @(posedge clk) tick=tick+1;
  stpu_top dut(.*);
  initial begin
    if(!$value$plusargs("directory=%s",directory)) $fatal(1,"missing directory");
    if(!$value$plusargs("ports=%d",ports)) ports=8;
    if(!$value$plusargs("qcount=%d",qcount)) qcount=3;
    if(qcount<1 || qcount>3) $fatal(1,"invalid RHS count");
    if(ports<=0 || NumOfCU%ports!=0) $fatal(1,"invalid port width");
    $readmemh({directory,"im.hex"},im);
    $readmemh({directory,"sm1.hex"},sm1);
    $readmemh({directory,"lengths.hex"},lengths);
    for(int u=0;u<NumOfCU;u++) begin
      for(int m=0;m<3;m++) if(lengths[m*NumOfCU+u]>max_load)max_load=lengths[m*NumOfCU+u];
      if(lengths[3*NumOfCU+u]>max_dm)max_dm=lengths[3*NumOfCU+u];
    end
    for(int q=0;q<qcount;q++) begin
      @(negedge clk);begin_tick=tick;rstn=0;start=0;dm_done_rd_en='0;
      im_init_wr_en='0;sm1_init_wr_en='0;sm2_init_wr_en='0;
      $readmemh({directory,$sformatf("sm2_%0d.hex",q)},sm2);
      repeat(4) @(negedge clk);
      rstn=1;
      for(int g=0;g<NumOfCU;g+=ports) begin
        group_load=0;
        for(int u=g;u<g+ports;u++)
          for(int m=0;m<3;m++)if(lengths[m*NumOfCU+u]>group_load)group_load=lengths[m*NumOfCU+u];
        for(int a=0;a<group_load;a++) begin
          @(negedge clk);
          im_init_wr_en='0;sm1_init_wr_en='0;sm2_init_wr_en='0;
          for(int u=g;u<g+ports;u++) begin
            im_init_wr_en[u]=(a<lengths[u]);
            sm1_init_wr_en[u]=(a<lengths[NumOfCU+u]);
            sm2_init_wr_en[u]=(a<lengths[2*NumOfCU+u]);
            im_init_wr_addr[u]=a;sm1_init_wr_addr[u]=a;sm2_init_wr_addr[u]=a;
            if(a<DEPTH_IM)im_init_wr_data[u]=im[u*DEPTH_IM+a];
            if(a<DEPTH_SM1)sm1_init_wr_data[u]=sm1[u*DEPTH_SM1+a];
            if(a<DEPTH_SM2)sm2_init_wr_data[u]=sm2[u*DEPTH_SM2+a];
          end
        end
      end
      @(negedge clk);im_init_wr_en='0;sm1_init_wr_en='0;sm2_init_wr_en='0;
      @(negedge clk);start=1;launch_tick=tick;count=0;
      while(!finish && count<20000) begin @(posedge clk);#1;count=count+1;end
      if(!finish)$fatal(1,"transaction timeout");
      end_tick=tick;
      fd=$fopen({directory,$sformatf("dm_%0d.hex",q)},"w");
      if(!fd)$fatal(1,"output open failure");
      for(int g=0;g<NumOfCU;g+=ports) begin
        group_dm=0;
        for(int u=g;u<g+ports;u++)if(lengths[3*NumOfCU+u]>group_dm)group_dm=lengths[3*NumOfCU+u];
        for(int a=0;a<group_dm;a++) begin
          @(negedge clk);dm_done_rd_en='0;
          for(int u=g;u<g+ports;u++)begin
            dm_done_rd_en[u]=(a<lengths[3*NumOfCU+u]);dm_done_rd_addr[u]=a;
          end
          @(posedge clk);#1;
          for(int u=g;u<g+ports;u++)
            if(a<lengths[3*NumOfCU+u])$fdisplay(fd,"%0d %0d %08x",u,a,dm_done_rd_data[u]);
        end
      end
      $fclose(fd);
      $display("TRANSACTION idx=%0d setup=%0d solve=%0d readback=%0d total=%0d",q,launch_tick-begin_tick,count,tick-end_tick,tick-begin_tick);
    end
    $finish;
  end
endmodule
