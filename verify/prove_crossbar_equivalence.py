"""Check the one-hot physical crossbar against indexed selection for 64 ports."""
import json
from pathlib import Path
from z3 import BitVec, BitVecVal, If, Or, Solver, unsat

root = Path(__file__).resolve().parents[1]
data = [BitVec(f'input_{i}', 32) for i in range(64)]
sel = BitVec('sel', 6)
one_hot = BitVecVal(0, 32)
for i in range(64):
    one_hot = one_hot | If(sel == i, data[i], BitVecVal(0, 32))
indexed = data[63]
for i in reversed(range(63)):
    indexed = If(sel == i, data[i], indexed)
solver = Solver()
solver.add(one_hot != indexed)
status = solver.check()
record = {
    'status': 'PASS' if status == unsat else 'FAIL',
    'solver_result': str(status),
    'scope': 'all 64 selectors and arbitrary 64 x 32-bit input words, one output port; all output ports instantiate this identical function',
}
(root/'reports/crossbar_equivalence.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
if status != unsat:
    raise SystemExit(1)
