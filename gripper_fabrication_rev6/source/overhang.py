import numpy as np, glob, json
res = {}
for f in sorted(glob.glob(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'..','stl','*.stl'))):
    import struct
    data = open(f, 'rb').read()
    if data[:5] == b'solid' and b'facet' in data[:300]:
        V = []
        for line in data.decode().splitlines():
            line = line.strip()
            if line.startswith('vertex'): V.append(list(map(float, line.split()[1:])))
        T = np.array(V).reshape(-1, 3, 3)
    else:
        n = struct.unpack('<I', data[80:84])[0]
        arr = np.frombuffer(data[84:84+n*50], dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')]))
        T = arr['v'].reshape(-1, 3, 3).astype(float)
    nrm = np.cross(T[:, 1]-T[:, 0], T[:, 2]-T[:, 0]); A = np.linalg.norm(nrm, axis=1)/2; nz = nrm[:, 2]/(2*A+1e-12)
    zc = T[:, :, 2].mean(1)
    down = (nz < -0.71) & (zc > 0.3)          # >45 deg overhang, not on bed
    flat = (nz < -0.99) & (zc > 0.3)
    # largest connected flat overhang approximated by bbox of flat-down triangles grouped by z
    groups = {}
    for i in np.where(flat)[0]:
        groups.setdefault(round(zc[i], 1), []).append(i)
    big = []
    for z, idx in groups.items():
        P = T[idx].reshape(-1, 3)[:, :2]; ext = P.max(0) - P.min(0)
        big.append((z, round(float(A[idx].sum()), 1), [round(e, 1) for e in ext]))
    big.sort(key=lambda t: -t[1])
    res[f.split('/')[-1]] = dict(overhang45_mm2=round(float(A[down].sum()), 1), flat_down_groups_top3=big[:3])
print(json.dumps(res, indent=1))
json.dump(res, open('overhang_report.json', 'w'), indent=1)
