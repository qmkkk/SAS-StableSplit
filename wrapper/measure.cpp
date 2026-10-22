#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <chrono>
#include <stdexcept>
#include "stpucpl.h"

template<class T> void dump(const std::string& p,const T* v,size_t n) {
  std::ofstream f(p,std::ios::binary); f.write(reinterpret_cast<const char*>(v),n*sizeof(T));
  if(!f) throw std::runtime_error("write failure "+p);
}
int main(int argc,char** argv) {
  if(argc<4) return 2;
  const auto begin=std::chrono::steady_clock::now();
  int n=0; int *rp=nullptr,*ci=nullptr; float *av=nullptr;
  if(StpuCpl_ReadMtx2CSR(argv[1],n,rp,ci,av)) return 3;
  StpuCpl_CSROrdering(n,rp,ci,av);
  Cstpucpl* c=new Cstpucpl; StpuCpl_Initialize(c);
  const int conf[]={150,1,6,6,3,7,10,10,3,1,1,1,12,1,0,0,1,0};
  for(int i=0;i<18;i++) c->cfg[i]=conf[i];
  c->cfg[15]=std::stoi(argv[2]);
  const int np=64,nnz=rp[n]; uint64 *im=nullptr;
  std::vector<int> ip(np+1),s1p(np+1),s2p(np+1),dp(np+1);
  std::vector<int> s1perm(nnz),diag(n),s2perm(n),dperm(n);
  auto start=std::chrono::steady_clock::now();
  int rc=StpuCpl_Configure(c,n,rp,ci,ip.data(),im,s1p.data(),s1perm.data(),diag.data(),s2p.data(),s2perm.data(),dp.data(),dperm.data());
  double compile_seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
  std::string out=argv[3]; std::ofstream f(out+".csv"); f<<std::setprecision(12);
  f<<"rc,n,nnz,cycles,compile_seconds,author_compile_seconds,time_medium_dfw,time_coarse_dfw,load_balance,data_reuse,constraints,conflicts_i,conflicts_o,nop_bank,nop_psum,nop_dag,nop_tail,nop_rf,nop_write,util_im,util_sm1,util_dm,ins_sum,ins_l,mem_smem_kb\n";
  f<<rc<<','<<n<<','<<nnz<<','<<c->cycles<<','<<compile_seconds<<','<<c->time_cpl<<','<<c->time_medium_dfw<<','<<c->time_coarse_dfw<<','<<c->load_balance<<','<<c->data_reuse<<','<<c->constraints<<','<<c->conflicts_i<<','<<c->conflicts_o<<','<<c->rto_nop_ins_b<<','<<c->rto_nop_ins_p<<','<<c->rto_nop_ins_d<<','<<c->rto_nop_ins_l<<','<<c->rto_nop_ins_r<<','<<c->rto_nop_ins_w<<','<<c->util_im<<','<<c->util_sm1<<','<<c->util_dm<<','<<c->ins_sum<<','<<c->ins_l<<','<<c->mem_smem_all<<'\n';
  if(rc) return 4;
  // Save exact compiler outputs; later validation must execute these instructions.
  dump(out+".im.bin",im,ip[np]); dump(out+".im_ptr.bin",ip.data(),ip.size());
  dump(out+".dm_perm.bin",dperm.data(),n); dump(out+".dm_ptr.bin",dp.data(),dp.size());
  std::vector<float> s1(nnz),s2(n),rhs(n,1.f);
  if(argc>4) {std::ifstream b(argv[4],std::ios::binary);b.read(reinterpret_cast<char*>(rhs.data()),n*sizeof(float));if(!b) return 5;}
  StpuCpl_SM1(true,n,nnz,av,s1perm.data(),diag.data(),s1.data());
  StpuCpl_SM2(n,rhs.data(),s2perm.data(),s2.data());
  dump(out+".sm1.bin",s1.data(),nnz);dump(out+".sm1_ptr.bin",s1p.data(),s1p.size());
  dump(out+".sm2.bin",s2.data(),n);dump(out+".sm2_ptr.bin",s2p.data(),s2p.size());
  dump(out+".rhs.bin",rhs.data(),n);
  std::cout<<"MEASURE cycles="<<c->cycles<<" compile="<<compile_seconds<<" total="<<std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()<<"\n";
  StpuCpl_Free(c); delete[] rp;delete[] ci;delete[] av;delete[] im;
}
