#include "stpucpl.h"
#include <vector>
#include <fstream>
#include <iostream>
#include <cstdlib>
#include <stdexcept>
using Rows=std::vector<std::vector<int>>;
extern void real_alloc(Cstpucpl*,bool,int,const int*,const int*,int,Rows&)
 asm("__real__Z10Node_AllocP8CstpucplbiPKiS2_iRSt6vectorIS3_IiSaIiEESaIS5_EE");
extern void wrap_alloc(Cstpucpl*,bool,int,const int*,const int*,int,Rows&)
 asm("__wrap__Z10Node_AllocP8CstpucplbiPKiS2_iRSt6vectorIS3_IiSaIiEESaIS5_EE");
void wrap_alloc(Cstpucpl* c,bool upper,int n,const int* rp,const int* ci,int np,Rows& rows) {
  real_alloc(c,upper,n,rp,ci,np,rows);
  std::cerr<<"ALLOC_HOOK upper="<<upper<<" n="<<n<<" np="<<np<<" outer="<<rows.size()<<"\n";
  if(const char* path=std::getenv("C22_ALLOCATION")) {
    std::ifstream f(path); int file_n,file_np;
    if(!(f>>file_n>>file_np)||file_n!=n||file_np!=np||rows.size()!=size_t(np)) throw std::runtime_error("allocation header mismatch");
    Rows assigned(np);std::vector<bool> seen(n,false);int u,i;
    while(f>>u>>i) {
      if(u<0||u>=np||i<0||i>=n||seen[i])throw std::runtime_error("invalid allocation");
      seen[i]=true;assigned[u].push_back(i);
    }
    for(bool s:seen)if(!s)throw std::runtime_error("missing node");
    rows.swap(assigned);
  }
  if(const char* path=std::getenv("C22_ALLOCATION_DUMP")) {
    std::ofstream f(path);f<<n<<' '<<np<<'\n';
    for(size_t u=0;u<rows.size();++u)for(int i:rows[u])f<<u<<' '<<i<<'\n';
  }
}
