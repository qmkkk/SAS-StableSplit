"""One frozen causal comparison: retain degree32 grouping, gate using readiness.

Classical eligibility/priority/auxiliary budget are unchanged. The only new
decision is whether to execute an admitted split. No compiler feedback search.
"""
import os, json, hashlib
from pathlib import Path
from datetime import datetime
os.environ['C22_CORE_DIR']='combined_degree_readiness_v1'
os.environ['C22_NAMES']='add20_L,add20_U,dw2048_L,dw2048_U,rajat04_L,rajat04_U,rajat19_L,rajat19_U'
os.environ['C22_MODES']='original,degree32,degree_ready32'
os.environ['C22_NATIVE']='1'
import core_screen as core
import numpy as np
from scipy.sparse import csr_matrix

original_transform=core.transform

def combined_transform(a,mode):
    if mode!='degree_ready32': return original_transform(a,mode)
    n=a.shape[0]; k=32
    lengths=np.diff(a.indptr)-1
    chosen=set();remaining=n//5
    for i in sorted(range(n),key=lambda i:(-lengths[i],i)):
        need=max(0,(int(lengths[i])-k+k-1)//k)
        if lengths[i]>2*k and 0<need<=remaining:
            chosen.add(i);remaining-=need
    ready=np.zeros(n,dtype=int);rows=[];rhs=[];mapping=[];selected=[]
    for i in range(n):
        pairs=list(zip(a.indices[a.indptr[i]:a.indptr[i+1]],a.data[a.indptr[i]:a.indptr[i+1]]))
        diagonal=[float(v) for j,v in pairs if j==i]
        assert len(diagonal)==1 and diagonal[0]!=0
        edges=[(int(j),float(v)) for j,v in pairs if j<i]
        assert len(edges)+1==len(pairs)
        raw=core.finish([ready[j] for j,v in edges]);groups=[]
        if i in chosen:
            early=edges[:-k];late=edges[-k:]
            proposed=[early[s:s+k] for s in range(0,len(early),k)]
            releases=[core.finish([ready[j] for j,v in g]) for g in proposed]
            predicted=core.finish(releases+[ready[j] for j,v in late])
            # Same 4-cycle admission margin as historical readiness16.
            if predicted+4<=raw:
                groups=proposed;edges=late
        aux=[];releases=[]
        for group in groups:
            z=len(rows)
            rows.append([(mapping[j],-v) for j,v in group]+[(z,1.0)])
            rhs.append(0.0);aux.append((z,1.0))
            releases.append(core.finish([ready[j] for j,v in group]))
        ready[i]=core.finish(releases+[ready[j] for j,v in edges])
        if groups:selected.append({'row':i,'groups':len(groups),'raw_finish':raw,'predicted_finish':int(ready[i])})
        idx=len(rows);mapping.append(idx)
        rows.append([(mapping[j],v) for j,v in edges]+aux+[(idx,diagonal[0])]);rhs.append(1.0)
    rr=[];cc=[];vv=[]
    for i,row in enumerate(rows):
        for j,v in row:rr.append(i);cc.append(j);vv.append(v)
    return csr_matrix((vv,(rr,cc)),shape=(len(rows),len(rows))),np.array(rhs,dtype=np.float32),np.array(mapping),selected

core.transform=combined_transform

if __name__=='__main__':
    manifest=core.OUT/'manifest.json'
    assert not manifest.exists(), 'use a separately documented resume; preserve first registration'
    sources={}
    for name in core.NAMES:
        p=core.ROOT/('experiments/paper_cases' if name.startswith('rajat') else 'vendor/stspu/sw/demo/benchmarks')/(name+'.mtx')
        sources[name]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    manifest.write_text(json.dumps({
       'registered_at':datetime.now().astimezone().isoformat(),
       'question':'Can a dependency-readiness filter on frozen degree32 improve the latency/auxiliary-state tradeoff?',
       'baselines':['original','degree32'],'candidate':'degree_ready32',
       'frozen_inputs':sources,'hardware_unchanged':True,'params':{'k':32,'auxiliary_budget':'floor(n/5)','margin':4},
       'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'paired_runner_sha256':hashlib.sha256(Path(core.__file__).read_bytes()).hexdigest(),
       'primary_measure':'Author compiler complete triangular-solve cycles at fixed configuration',
       'costs':['auxiliary nodes','instructions','SM1/DM/IM occupancy','transformation seconds','compiler seconds'],
       'correctness':'Original factor float64 residual now; hardware FP32 correctness required before performance claim',
       'decision':'Advance on meaningful whole-solve / storage tradeoff improvement with explanation; no universal-win requirement. A null filter does not invalidate the degree-splitting route.',
       'no_new_baseline_families':True,'no_parameter_sweep':True,'prior_evidence_read_only':True
    },ensure_ascii=False,indent=2),encoding='utf8')
    core.main()
