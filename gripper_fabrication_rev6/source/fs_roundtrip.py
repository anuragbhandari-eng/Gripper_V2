"""Parse partSpecs() from the generated .fs and rebuild with CadQuery: verifies encoding + reports volumes."""
import re, json, numpy as np
from prims import cq_part, PT
src = open('LeadScrewGripper.fs').read()
body = src[src.index('function partSpecs()'):]
arr = body[body.index('return [')+7: body.rindex('];')+1]
js = re.sub(r'"(\w+)"\s*:', r'"\1":', arr).replace('true', 'true').replace('false', 'false')
js = re.sub(r',\s*\]', ']', js)
specs = json.loads(js)
import design as D
minseg = 1e9; out = {}
for sp in specs:
    ops = []
    for o in sp['ops']:
        op = 'add' if o[0] == 1 else 'cut'
        if o[1] in ('ext', 'extx'):
            cur = np.array(o[2]); segs = []
            for s in o[3]:
                end = np.array(s[1:3] if s[0] == 0 else s[3:5]); minseg = min(minseg, np.linalg.norm(end-cur)); cur = end
                segs.append(('L', PT(*s[1:3])) if s[0] == 0 else ('A', PT(*s[1:3]), PT(*s[3:5])))
            ops.append((op, (o[1], dict(start=PT(*o[2]), segs=segs), o[4], o[5])))
        elif o[1] == 'cyl': ops.append((op, ('cyl', tuple(o[2]), tuple(o[3]), o[4])))
        else: ops.append((op, ('box', tuple(o[2]), tuple(o[3]))))
    s = cq_part(ops); out[sp['name']] = round(s.Volume(), 1)
print('min segment length in any loop: %.4f mm' % minseg)
print(json.dumps(out, indent=0))
json.dump(out, open('fs_volumes.json', 'w'), indent=1)
