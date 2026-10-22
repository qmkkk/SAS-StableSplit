#include "stpucpl.h"
#include <fstream>
#include <vector>
#include <iostream>
int main(int argc,char** argv) {
  if(argc!=5)return 2;
  int n=std::stoi(argv[1]);std::vector<float> dm(n),x(n);std::vector<int> perm(n);
  std::ifstream a(argv[2],std::ios::binary),b(argv[3],std::ios::binary);
  a.read(reinterpret_cast<char*>(dm.data()),n*4);b.read(reinterpret_cast<char*>(perm.data()),n*4);
  if(!a||!b)return 3;
  int rc=StpuCpl_DM(n,dm.data(),perm.data(),x.data());if(rc)return 4;
  std::ofstream c(argv[4],std::ios::binary);c.write(reinterpret_cast<char*>(x.data()),n*4);
  return c?0:5;
}
