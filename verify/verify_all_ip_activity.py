"""Reassemble and check five saved AMD-IP SAIF runs without rerunning simulation."""
from pathlib import Path
import hashlib
import json
import re

S=Path(__file__).resolve().parents[1]
cases=json.loads((S/'reports/program_registration.json').read_text())['rows']
reference=json.loads((S/'reports/activity_verification.json').read_text())['rows']
byname={r['task']+'_'+r['mode']:r for r in reference}
rows=[]
for case in cases:
    name=case['task']+'_'+case['mode']
    folder=S/'experiments/programs'/name
    log=(folder/'simulate32_ip.log').read_text(errors='replace')
    match=re.findall(r'TRANSACTION idx=(\d+) setup=(\d+) solve=(\d+) readback=(\d+) total=(\d+)',log)
    assert len(match)==1 and match[0][0]=='0',name
    assert [int(v) for v in match[0][1:4]]==[
        byname[name]['setup_cycles'],byname[name]['solve_cycles'],
        byname[name]['readback_cycles']],name
    cycles=int(match[0][4])
    assert cycles==byname[name]['total_cycles'],name
    saif=folder/'activity32_ip.saif'
    header=saif.open(encoding='utf8',errors='replace').read(600)
    units=re.search(r'\(TIMESCALE\s+(\d+)\s+(fs|ps|ns|us)\)',header)
    duration=re.search(r'\(DURATION\s+(\d+)\)',header)
    assert units and duration
    scale={'fs':1e-15,'ps':1e-12,'ns':1e-9,'us':1e-6}[units[2]]
    seconds=int(duration[1])*int(units[1])*scale
    assert abs(seconds-byname[name]['activity_seconds'])<1e-12,name
    binary=(folder/'active_dm.bin').read_bytes()
    output={}
    for line in (folder/'dm_0.hex').read_text().splitlines():
        cu,addr,word=line.split()
        output[(int(cu),int(addr))]=int(word,16)
    import numpy as np
    ptr=np.fromfile(Path(case['prefix']).with_suffix('.dm_ptr.bin'),dtype='<i4')
    words=np.array([output[cu,addr] for cu in range(32)
                    for addr in range(int(ptr[cu+1]-ptr[cu]))],dtype='<u4')
    assert words.tobytes()==binary,(name,'AMD-IP output differs from behavioral reference')
    rows.append({'task':case['task'],'mode':case['mode'],'cycles':cycles,
                 'exact_amd_ip_output_matches_behavioral':True,
                 'componentwise_backward_error':byname[name]['componentwise_backward_error'],
                 'seconds':seconds,'saif_bytes':saif.stat().st_size,
                 'saif_sha256':hashlib.sha256(saif.read_bytes()).hexdigest(),
                 'saif':str(saif)})
result={'status':'PASS','scope':'five registered 32-CU cold one-RHS AMD-IP simulations, exact output and phase-cycle checks',
        'rows':rows}
(S/'reports/ip_activity_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({'status':'PASS','cases':len(rows),'saif_gb':round(sum(r['saif_bytes'] for r in rows)/1e9,3)}))
