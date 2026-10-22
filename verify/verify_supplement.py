from pathlib import Path
import json, hashlib, sys
import numpy as np
from scipy.io import mmread
H=Path(__file__).resolve().parents[1]; C=H.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=[]
for p in (C/'experiments/mej_affinity_v1').glob('*_budget_0.mtx'):
 task=p.name[:-len('_budget_0.mtx')]; q=p.with_suffix(''); mapping=np.load(q.with_suffix('.mapping.npy'))
 alloc=np.loadtxt(q.with_suffix('.allocation.txt'),skiprows=1,dtype=int)
 rootset=set(mapping); aux=[i for i in range(len(alloc)) if i not in rootset]
 seed=json.loads(q.with_suffix('.placement.json').read_text())
 for mode in ['budget_0','budget_1','budget_5','budget_10','budget_100','affinity_1']:
  z=p.parent/(task+'_'+mode); a=np.loadtxt(z.with_suffix('.allocation.txt'),skiprows=1,dtype=int)
  info=json.loads(z.with_suffix('.placement.json').read_text())
  assert sha(p)==sha(z.with_suffix('.mtx'))
  assert np.array_equal(mapping,np.load(z.with_suffix('.mapping.npy')))
  assert np.array_equal(alloc[:,1],a[:,1])
  assert np.array_equal(np.array(seed['final_cu'])[aux],np.array(info['final_cu'])[aux])
  assert info['migrations']<=info['budget']
 old=next(C/'experiments'/d/(task+'_stable_split') for d in ['stable_split_v1','stable_independent_v1'] if (C/'experiments'/d/(task+'_stable_split.im.bin')).exists())
 remap=next(C/'experiments'/d/(task+'_free_work') for d in ['free_allocation_v1','stable_split_v1','stable_independent_v1'] if (C/'experiments'/d/(task+'_free_work.mtx')).exists())
 assert sha(p)==sha(remap.with_suffix('.mtx'))
 assert np.array_equal(mapping,np.load(remap.with_suffix('.mapping.npy')))
 bins=[x for x in p.parent.glob(task+'_budget_0.*.bin') if x.name.endswith(('.im.bin','.im_ptr.bin','.sm1.bin','.sm1_ptr.bin','.sm2.bin','.sm2_ptr.bin','.dm_ptr.bin','.dm_perm.bin','.row_order.bin'))]
 for b in bins:
  suffix=b.name[len(task+'_budget_0'):]; assert sha(b)==sha(Path(str(old)+suffix)),b.name
 out.append({'task':task,'identical_split_graphs':6,'also_identical_to_frozen_full_remap_graph':True,'identical_global_order':True,'auxiliary_map_fixed':True,'budget_caps_pass':True,'stable_binary_files_identical':len(bins)})
assert len(out)==21
order=[]
compiled=json.loads((C/'experiments/mej_order_v1/summary.json').read_text())
for x in compiled:
 t=x['task']; a=mmread(x['source_path']).tocsr()
 if x['source_implicit_unit_diagonal']:
  from scipy.sparse import eye
  a=a+eye(a.shape[0],format='csr')
 case=H/'experiments/rtl_order'/(t+'_remap_stable_order')
 for k in range(3):
  b=np.load(case/f'original_rhs_{k}.npy').astype(float); y=np.load(case/f'solution_{k}.npy').astype(float)
  e=float(max(abs(a@y-b)/(abs(a)@abs(y)+abs(b)+np.finfo(float).tiny)))
  assert np.isfinite(y).all() and e<=1e-5
  order.append({'task':t,'rhs':k,'backward_error':e,'pass':True})
result={'fairness':out,'independent_order_checks':order,'passed':True}
(H/'reports/fairness_verification.json').write_text(json.dumps(result,indent=2))
print('PASS',len(out),'input graph/order/map/binary contracts;',len(order),'independent order checks')
