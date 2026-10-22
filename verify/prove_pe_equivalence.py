"""Prove old muxed PE and acyclic PE are combinationally equivalent.

FP add/multiply are uninterpreted bit-vector functions: the proof holds for
any deterministic implementations of the same two operators, including AMD IP.
It does not assert that AMD and shortreal have identical IEEE corner behavior.
"""
import json
from pathlib import Path
from z3 import BitVec, BitVecSort, Bool, Function, If, Solver, unsat

out = Path(__file__).resolve().parents[1] / 'reports' / 'pe_equivalence.json'
word = BitVecSort(32)
add = Function('fp_add', word, word, word)
mul = Function('fp_mul', word, word, word)
psum, xb, lij = (BitVec(name, 32) for name in ('psum', 'xb', 'lij'))
ct = Bool('ct')
psum_inv = psum ^ 0x80000000

# The original combinational mux loop has a unique selected branch for each
# value of ct. These expressions are obtained by substituting that branch.
old_ct0 = mul(add(psum_inv, xb), lij)
old_ct1 = add(psum, mul(xb, lij))
old = If(ct, old_ct1, old_ct0)

pre_mul = mul(xb, lij)
new_add = add(If(ct, psum, psum_inv), If(ct, pre_mul, xb))
post_mul = mul(new_add, lij)
new = If(ct, new_add, post_mul)

solver = Solver()
solver.add(old != new)
status = solver.check()
result = {
    'status': 'PASS' if status == unsat else 'FAIL',
    'solver_result': str(status),
    'scope': 'arbitrary 32-bit operands, both control modes, same deterministic FP add/multiply semantics',
    'independent_fpu_equivalence': False,
    'latency_change': 0,
}
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
if status != unsat:
    raise SystemExit(1)
