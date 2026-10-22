"""Summarize same-device routed AMD-IP SAIF power and transaction energy."""
from pathlib import Path
import csv
import json
import re

S=Path(__file__).resolve().parents[1]
rows=json.loads((S/'reports/ip_activity_verification.json').read_text())['rows']
out=[]
for row in rows:
    name=row['task']+'_'+row['mode']
    folder=S/'experiments/programs'/name
    report=(folder/'power_ip.rpt').read_text(errors='replace')
    def value(label):
        m=re.search(r'^\|\s*'+re.escape(label)+r'\s*\|\s*([^|]+?)\s*\|',report,re.M)
        assert m,(name,label)
        return m.group(1).strip()
    total=float(value('Total On-Chip Power (W)'))
    dynamic=float(value('Dynamic (W)'))
    static=float(value('Device Static (W)'))
    matched=value('Design Nets Matched')
    fraction=int(re.search(r'(\d+)%',matched)[1])/100
    confidence=value('Confidence Level')
    regs=(folder/'register_activity_ip.rpt').read_text(errors='replace')
    reg_total=len(regs.splitlines())
    reg_sim=sum('(S)' in line for line in regs.splitlines())
    out.append({'task':row['task'],'mode':row['mode'],'cycles':row['cycles'],
                'duration_s':row['seconds'],'total_w':total,'dynamic_w':dynamic,
                'static_w':static,'estimated_total_uJ':total*row['seconds']*1e6,
                'estimated_dynamic_uJ':dynamic*row['seconds']*1e6,
                'matched_nets_fraction':fraction,'register_simulated_fraction':reg_sim/reg_total,
                'confidence':confidence,'backward_error':row['componentwise_backward_error']})
bykey={(r['task'],r['mode']):r for r in out}
for r in out:
    base=bykey[(r['task'],'free_work')]
    r['cycles_reduction_vs_remap_pct']=100*(base['cycles']-r['cycles'])/base['cycles']
    r['estimated_energy_reduction_vs_remap_pct']=100*(base['estimated_total_uJ']-r['estimated_total_uJ'])/base['estimated_total_uJ']
    r['estimated_dynamic_energy_reduction_vs_remap_pct']=100*(base['estimated_dynamic_uJ']-r['estimated_dynamic_uJ'])/base['estimated_dynamic_uJ']
status='PASS' if len(out)==5 and all(r['confidence'] in {'High','Medium'} for r in out) else 'FAIL'
result={'status':status,'scope':'routed 32-CU on-chip Vivado estimates at 10 MHz, typical process, 25 C; no board or 64-CU extrapolation',
        'qualification':'medium confidence; sparse SAIF annotation and unknown-valued inactive storage prevent measured-energy claims',
        'rows':out}
(S/'reports/power_analysis.json').write_text(json.dumps(result,indent=2),encoding='utf8')
with (S/'reports/power_analysis.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print(json.dumps({'status':status,'rows':len(out),
                  'comparison':[(r['task'],r['mode'],round(r['estimated_energy_reduction_vs_remap_pct'],2)) for r in out]},indent=2))
