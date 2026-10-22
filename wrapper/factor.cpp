#include "cktso.h"
#include <vector>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <string>
template<class T> void read(std::ifstream&f,std::vector<T>&a){f.read((char*)a.data(),a.size()*sizeof(T));}
void out(const std::string&p,int n,const std::vector<size_t>&rp,const std::vector<int>&ci,const std::vector<double>&v,bool upper){
 std::ofstream f(p);f<<std::setprecision(17)<<"%%MatrixMarket matrix coordinate real general\n"<<n<<' '<<n<<' '<<v.size()+(upper?n:0)<<'\n';
 for(int i=0;i<n;i++){if(upper)f<<i+1<<' '<<i+1<<" 1\n";for(size_t k=rp[i];k<rp[i+1];k++)f<<i+1<<' '<<ci[k]+1<<' '<<v[k]<<'\n';}
}
int main(int argc,char**argv){
 if(argc!=3)return 2;std::ifstream f(argv[1],std::ios::binary);int n,nnz;f.read((char*)&n,4);f.read((char*)&nnz,4);
 std::vector<int> rp(n+1),ci(nnz);std::vector<double>a(nnz);read(f,rp);read(f,ci);read(f,a);if(!f)return 3;
 ICktSo c=nullptr;int*ip;const long long*op;int rc=CKTSO_CreateSolver(&c,&ip,&op);if(rc<0){std::cout<<"create "<<rc<<std::endl;return 4;}
 rc=c->Analyze(false,n,rp.data(),ci.data(),a.data(),1);if(rc<0){std::cout<<"analyze "<<rc<<std::endl;return 5;}
 rc=c->Factorize(a.data(),false);if(rc<0){std::cout<<"factor "<<rc<<std::endl;return 6;}
 std::vector<size_t>lp(n+1),up(n+1);std::vector<int>li(op[5]),ui(op[6]);std::vector<double>lx(op[5]),ux(op[6]);
 rc=c->ExtractFactors(lp.data(),li.data(),lx.data(),up.data(),ui.data(),ux.data(),nullptr,nullptr,nullptr,nullptr);if(rc<0)return 7;
 out(std::string(argv[2])+"_L.mtx",n,lp,li,lx,false);out(std::string(argv[2])+"_U.mtx",n,up,ui,ux,true);
 std::cout<<"n="<<n<<" L="<<op[5]<<" U_no_diag="<<op[6]<<std::endl;c->DestroySolver();return 0;
}
