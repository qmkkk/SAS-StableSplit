"""Direct allocation on the unchanged author medium/coarse backend.

free_work is the mature least-workload allocation control (AG-SpTRSV).
free_edge uses classical critical-path list scheduling with edge-ready costs.
Neither classical rule is claimed as a newly invented scheduling algorithm.
The experiment tests the restriction imposed by FIFO-encoded joint placement.
"""
from pathlib import Path
from datetime import datetime
import json, os, heapq, hashlib
import numpy as np
import final_joint_method as retained
p=retained.p;core=p.core;root=core.ROOT
out=root/'experiments'/os.environ.get('C22_FREE_OUT','free_allocation_v1')
out.mkdir(exist_ok=True);current=''

def allocation(a,mode):
    n=a.shape[0];weights=np.diff(a.indptr).astype(int)
    fifo,children=p.fifo(a)
    parents=[a.indices[a.indptr[i]:a.indptr[i+1]-1] for i in range(n)]
    rank=weights.copy()
    for i in range(n-1,-1,-1):
        if children[i]:rank[i]+=max(rank[j] for j in children[i])
    loads=np.zeros(64,int);counts=np.zeros(64,int);available=np.zeros(64,int)
    done=np.zeros(n,int);assign=np.full(n,-1,int);order=[]
    remaining=weights-1;ready=[]
    for i in np.flatnonzero(remaining==0):heapq.heappush(ready,(-int(rank[i]),int(i)))
    while len(order)<n:
        if mode=='free_work':i=int(fifo[len(order)])
        else:_,i=heapq.heappop(ready)
        eligible=[u for u in range(64) if counts[u]<128 and loads[u]+weights[i]<=1024]
        if not eligible:raise RuntimeError('greedy placement capacity exhausted')
        releases=sorted(int(done[j]) for j in parents[i]);d=len(releases)
        tail=max((v+d-k+1 for k,v in enumerate(releases)),default=1)
        if mode=='free_work':u=min(eligible,key=lambda u:(int(loads[u]),int(counts[u]),u))
        else:u=min(eligible,key=lambda u:(max(int(available[u])+d+1,tail),int(loads[u]),u))
        done[i]=max(int(available[u])+d+1,tail);available[u]=done[i]
        loads[u]+=weights[i];counts[u]+=1;assign[i]=u;order.append(i)
        if mode!='free_work':
            for j in children[i]:
                remaining[j]-=1
                if remaining[j]==0:heapq.heappush(ready,(-int(rank[j]),int(j)))
    return assign,order,{'max_cu_work':int(max(loads)),'max_cu_rows':int(max(counts)),
      'cu_work':loads.tolist(),'estimated_finish':int(max(done))}

def transform(a,mode):
    b,rhs,mapping,selected=retained.transform(a,'degree32')
    assign,order,info=allocation(b,mode)
    prefix=out/(current+'_'+mode)
    prefix.with_suffix('.allocation.txt').write_text(f'{b.shape[0]} 64\n'+''.join(f'{assign[i]} {i}\n' for i in order))
    prefix.with_suffix('.placement.json').write_text(json.dumps(info,indent=2))
    return b,rhs,mapping,selected

if __name__=='__main__':
    names=os.environ.get('C22_FREE_NAMES','dw2048_L,rajat19_L,fpga_dcop_01_L,bayer07_L').split(',')
    modes=os.environ.get('C22_FREE_MODES','free_work,free_edge').split(',')
    manifest=out/'manifest.json'
    if not manifest.exists():manifest.write_text(json.dumps({'at':datetime.now().astimezone().isoformat(),
      'question':'Does removing FIFO-cyclic allocation constraints resolve split/placement interference on the unchanged strong backend?',
      'fixed_inputs':names,'modes':modes,'mature_control':'free_work: AG-SpTRSV least-workload module adapted to STSPU',
      'candidate':'free_edge: critical-list edge-ready allocation of the same split graph',
      'retained_comparator':'degree32 plus balanced FIFO allocation',
      'hardware':'same 64 CUs and all memories, same author psum/ICR scheduler',
      'decision':'complete verified transaction, including auxiliary storage load/readback; no promotion based on proxy cycles',
      'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
    core.OUT=out;core.transform=transform
    core.linux=lambda path:p.old_linux(root/'experiments/measure_allocation' if Path(path).name=='measure' else path)
    for name in names:
        current=name
        if name in ['fpga_dcop_01_L','bayer07_L','bcsstm10_L','add32_L']:os.environ['C22_INPUT_DIR']=str(root/'experiments/joint_heldout_inputs_v1')
        elif name not in ['add20_L','dw2048_L','rajat04_L','rajat19_L']:os.environ['C22_INPUT_DIR']=str(root/'formal_joint_20261021/table_inputs')
        else:os.environ.pop('C22_INPUT_DIR',None)
        core.NAMES=[name];core.MODES=modes;core.main()
