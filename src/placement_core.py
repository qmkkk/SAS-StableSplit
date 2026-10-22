"""Encode balanced FIFO-frontier scheduling through semantics-preserving relabeling.

The author backend's observed FIFO topological traversal assigns position q to
CU q mod 64. Permute only the group of nodes released by one processed node.
Relabeling in the resulting traversal order reproduces that traversal by
induction. The selection within each group adapts classical workload balancing.
"""
from pathlib import Path
from datetime import datetime
from collections import deque
import json,heapq,hashlib,os
import numpy as np
os.environ['C22_CORE_DIR']='joint_placement_v1'
import core_screen as core
import combined_core as previous
core.OUT=core.ROOT/'experiments/joint_placement_v1';core.OUT.mkdir(exist_ok=True)
core.NAMES=[];core.MODES=[]
os.environ['C22_NATIVE']='1'
current=''
old_linux=core.linux
core.linux=lambda p:old_linux(core.ROOT/'experiments/measure_metadata' if Path(p).name=='measure' else p)

def fifo(a):
    n=a.shape[0];degree=np.diff(a.indptr)-1
    children=[[] for _ in range(n)]
    for i in range(n):
        for j in a.indices[a.indptr[i]:a.indptr[i+1]]:
            if j<i:children[j].append(i)
    q=deque(int(i) for i in np.flatnonzero(degree==0));order=[]
    while q:
        i=q.popleft();order.append(i)
        for j in children[i]:
            degree[j]-=1
            if degree[j]==0:q.append(j)
    assert len(order)==n
    return np.array(order),children

def balanced_frontiers(a):
    n=a.shape[0];weights=np.diff(a.indptr).astype(int)
    old_order,children=fifo(a)
    before=np.zeros(64,int)
    for pos,i in enumerate(old_order):before[pos%64]+=weights[i]
    remaining=weights.copy()-1;loads=np.zeros(64,int);queue=deque();order=[]
    def enqueue(nodes):
        if not nodes:return
        start=len(order)+len(queue)
        positions={}
        for pos in range(len(nodes)):positions.setdefault((start+pos)%64,deque()).append(pos)
        heap=[(int(loads[cu]),q[0],cu) for cu,q in positions.items()];heapq.heapify(heap)
        arranged=[None]*len(nodes)
        for node in sorted(nodes,key=lambda i:(-weights[i],i)):
            _,_,cu=heapq.heappop(heap);pos=positions[cu].popleft()
            arranged[pos]=node;loads[cu]+=weights[node]
            if positions[cu]:heapq.heappush(heap,(int(loads[cu]),positions[cu][0],cu))
        queue.extend(arranged)
    enqueue([int(i) for i in np.flatnonzero(remaining==0)])
    batch_sizes=[]
    while queue:
        i=queue.popleft();order.append(i);released=[]
        for j in children[i]:
            remaining[j]-=1
            if remaining[j]==0:released.append(j)
        batch_sizes.append(len(released));enqueue(released)
    assert len(order)==n
    order=np.array(order);inverse=np.empty(n,int);inverse[order]=np.arange(n)
    b=a[order,:][:,order].tocsr();b.sort_indices()
    assert all(np.all(b.indices[b.indptr[i]:b.indptr[i+1]]<=i) for i in range(n))
    new_order,_=fifo(b)
    assert np.array_equal(new_order,np.arange(n)), 'constructive traversal property'
    return b,order,inverse,{'before_max_cu_work':int(max(before)),'after_max_cu_work':int(max(loads)),
     'before_cu_work':before.tolist(),'after_cu_work':loads.tolist(),'release_groups_with_choice':sum(v>1 for v in batch_sizes),
     'traversal_property_verified':True}

def transform(a,mode):
    if mode=='balanced_degree32':base='degree32'
    elif mode=='balanced_filtered32':base='degree_ready32'
    else:raise ValueError(mode)
    b,rhs,mapping,selected=previous.combined_transform(a,base)
    b,order,inverse,info=balanced_frontiers(b)
    mapping=inverse[mapping]
    info.update(task=current,method=mode,base=base,old_node_in_new_order=order.tolist())
    (core.OUT/(current+'_'+mode+'.placement.json')).write_text(json.dumps(info,indent=2),encoding='utf8')
    return b,rhs[order].copy(),mapping,selected

core.transform=transform
if __name__=='__main__':
    names=['add20_L','add20_U','dw2048_L','dw2048_U','rajat04_L','rajat04_U','rajat19_L','rajat19_U']
    modes=['balanced_degree32','balanced_filtered32']
    manifest=core.OUT/'manifest.json';assert not manifest.exists()
    manifest.write_text(json.dumps({'registered_at':datetime.now().astimezone().isoformat(),
      'problem':'Splitting or contracting long rows perturbs FIFO cyclic CU placement and can concentrate mutually delaying work.',
      'mechanism':'Construct workload-balanced release groups; encode their FIFO traversal with a triangular row/column relabeling.',
      'origins':['AG-SpTRSV author least-workload scheduling module','DPU-v2 dependency/resource compatibility principle'],
      'coupling':'Apply the placement construction to each resulting partition, not to the pre-split graph.',
      'baselines':'Frozen original and degree32 results, unchanged author library and config',
      'candidates':modes,'inputs':names,'parameter_search':False,
      'decisive_observations':['actual CU assignment matches the constructed assignment','the previously colliding rows cease competing or become less blocking','whole-solve output and progress remain correct','intermediate state/capacity and transformation costs retained'],
      'method_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'code_boundary':'FIFO cyclic backend contract observed on both retained rajat19 graphs; will validate actual mappings on new outputs, not assume arbitrary backends.'},indent=2),encoding='utf8')
    for name in names:
        current=name
        core.NAMES=[name];core.MODES=modes
        core.main()
