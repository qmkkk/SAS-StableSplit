"""Preserve original-row CU ownership while placing only new partial sums.

The causal question is whether splitting needs to remap unrelated original
rows at all. Mature base: FIFO least-workload scheduling. Allocation of newly
introduced tasks uses residual coefficient capacity after reserving all roots.
"""
from pathlib import Path
from datetime import datetime
import json,os,hashlib
import numpy as np
import free_allocation_core as f
core=f.core;p=f.p;root=f.root;current=''
out=root/'experiments'/os.environ.get('C22_STABLE_OUT','stable_split_v1');out.mkdir(exist_ok=True)
def transform(a,mode):
    original_cu,oldorder,baseinfo=f.allocation(a,'free_work')
    if mode=='placement_only':
        b,rhs,mapping,selected=f.retained.transform(a,'original');cu=original_cu;order=oldorder
    elif mode in ['stable_split','stable_fifo']:
        b,rhs,mapping,selected=f.retained.transform(a,'degree32')
        cu=np.full(b.shape[0],-1,int);cu[mapping]=original_cu;weights=np.diff(b.indptr)
        load=np.bincount(original_cu,weights=weights[mapping],minlength=64).astype(int)
        count=np.bincount(original_cu,minlength=64)
        order,_=p.fifo(b)
        # Original row ownership and order are preserved. The positions of new
        # auxiliary rows are topological; only these rows can choose a new CU.
        if mode=='stable_split':
            expanded=[];start=0
            for i in range(a.shape[0]):
                expanded.append(list(range(start,int(mapping[i])+1)));start=int(mapping[i])+1
            order=[node for i in oldorder for node in expanded[i]]
        for i in order:
            if cu[i]>=0:continue
            eligible=[u for u in range(64) if count[u]<128 and load[u]+weights[i]<=1024]
            if not eligible:raise RuntimeError('stable root reservation exceeds capacity')
            u=min(eligible,key=lambda u:(int(load[u]),int(count[u]),u));cu[i]=u;load[u]+=weights[i];count[u]+=1
    else:raise ValueError(mode)
    prefix=out/(current+'_'+mode)
    prefix.with_suffix('.allocation.txt').write_text(f'{b.shape[0]} 64\n'+''.join(f'{cu[i]} {i}\n' for i in order))
    prefix.with_suffix('.placement.json').write_text(json.dumps({'original_CU_preserved':bool(np.array_equal(cu[mapping],original_cu)),'original_cu':original_cu.tolist()},indent=2))
    return b,rhs,mapping,selected
if __name__=='__main__':
    names=os.environ.get('C22_STABLE_NAMES','dw2048_L,rajat19_L,fpga_dcop_01_L,bayer07_L').split(',')
    modes=os.environ.get('C22_STABLE_MODES','placement_only,stable_split,stable_fifo').split(',')
    manifest=out/'manifest.json'
    if not manifest.exists():manifest.write_text(json.dumps({'at':datetime.now().astimezone().isoformat(),'inputs':names,'modes':modes,
      'problem':'Adding partial sums perturbs original-row assignment; preserve those CU identities to isolate splitting from unrelated remapping',
      'baselines':['no split plus least-work allocation','degree32 plus least-work allocation'],
      'candidate':'reserve original roots on their pre-split CUs, place new partial sums into residual capacity',
      'order_ablation':'stable_split preserves original per-CU root order; stable_fifo uses expanded FIFO',
      'decision':'full verified RTL transaction; no task-specific oracle selection',
      'origins':['STSPU V-E granularity tradeoff','AG-SpTRSV least-work scheduling','DPU-v2 dependency/resource mapping'],
      'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
    core.OUT=out;core.transform=transform
    core.linux=lambda path:p.old_linux(root/'experiments/measure_allocation' if Path(path).name=='measure' else path)
    for name in names:
        current=name
        if name in ['fpga_dcop_01_L','bayer07_L','bcsstm10_L','add32_L']:os.environ['C22_INPUT_DIR']=str(root/'experiments/joint_heldout_inputs_v1')
        elif name not in ['add20_L','dw2048_L','rajat04_L','rajat19_L']:os.environ['C22_INPUT_DIR']=str(root/'formal_joint_20261021/table_inputs')
        else:os.environ.pop('C22_INPUT_DIR',None)
        core.NAMES=[name];core.MODES=modes;core.main()
