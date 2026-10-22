"""Frozen core: degree32 partition plus realizable FIFO-frontier allocation.

No learned/adaptive admission, no schedule search, one backend compilation.
The auxiliary-node budget is shared with degree32 and checked against the
fixed total DM/SM2 capacity. A graph exceeding that capacity is left unsplit.
"""
import placement_core as p

def transform(a,mode):
    if mode=='original':return p.previous.original_transform(a,'original')
    b,rhs,mapping,selected=p.previous.original_transform(a,'degree32')
    if b.shape[0]>64*128:
        b,rhs,mapping,selected=p.previous.original_transform(a,'original')
    if mode=='degree32':return b,rhs,mapping,selected
    if mode!='joint':raise ValueError(mode)
    b,order,inverse,info=p.balanced_frontiers(b)
    return b,rhs[order].copy(),inverse[mapping],selected
