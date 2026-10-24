import sys, json
sys.path.insert(0, '.')
import check as C
res = C.clearance(41, 0.8)
out = {'|'.join(k): v for k, v in sorted(res.items(), key=lambda kv: kv[1][0])}
json.dump(out, open('clearance_rev.json', 'w'), indent=1)
for k, v in out.items(): print(f'{v[0]:6.3f} mm @ {v[1]:6.1f} deg  {k}')
