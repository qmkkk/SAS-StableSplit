// Export factor permutations/scaling and an independent author-solver reference.
#define main retained_factor_main
#include "factor.cpp"
#undef main
template<class T> void savevec(const std::string&p,const std::vector<T>&a){std::ofstream f(p,std::ios::binary);f.write((const char*)a.data(),a.size()*sizeof(T));if(!f)throw std::runtime_error("write "+p);}
int main(int argc,char**argv){
 if(argc!=4)return 2;std::ifstream f(argv[1],std::ios::binary);int n,nnz;f.read((char*)&n,4);f.read((char*)&nnz,4);
 std::vector<int>rp(n+1),ci(nnz);std::vector<double>a(nnz);read(f,rp);read(f,ci);read(f,a);if(!f)return 3;
 ICktSo c=nullptr;int*ip;const long long*op;int rc=CKTSO_CreateSolver(&c,&ip,&op);if(rc<0)return 4;
 rc=c->Analyze(false,n,rp.data(),ci.data(),a.data(),1);if(rc<0){std::cout<<"analyze "<<rc;return 5;}
 rc=c->Factorize(a.data(),false);if(rc<0){std::cout<<"factor "<<rc;return 6;}
 std::vector<size_t>lp(n+1),up(n+1);std::vector<int>li(op[5]),ui(op[6]),pr(n),pc(n);std::vector<double>lx(op[5]),ux(op[6]),rs(n,1),cs(n,1);
 rc=c->ExtractFactors(lp.data(),li.data(),lx.data(),up.data(),ui.data(),ux.data(),pr.data(),pc.data(),rs.data(),cs.data());if(rc<0)return 7;
 std::string prefix=argv[2];out(prefix+"_L.mtx",n,lp,li,lx,false);out(prefix+"_U.mtx",n,up,ui,ux,true);
 savevec(prefix+".rperm.bin",pr);savevec(prefix+".cperm.bin",pc);savevec(prefix+".rscale.bin",rs);savevec(prefix+".cscale.bin",cs);
 std::ifstream bf(argv[3],std::ios::binary);std::vector<double>b(n),x(n);
 for(int q=0;q<3;q++){read(bf,b);if(!bf)return 8;rc=c->Solve(b.data(),x.data(),true,false);if(rc<0)return 9;savevec(prefix+".reference"+std::to_string(q)+".bin",x);}
 std::cout<<"n="<<n<<" L="<<op[5]<<" U_no_diag="<<op[6]<<" scaling_setting="<<ip[7]<<std::endl;c->DestroySolver();return 0;
}
