import json, re, sys, unicodedata
gn_path, cp_path, dec_path, out_path = sys.argv[1:5]
def norm(s):
    s = unicodedata.normalize('NFD', s).encode('ascii','ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+',' ', s).strip()
    s = re.sub(r'\bste\b','sainte', re.sub(r'\bst\b','saint', s))
    return s
gn = [c for c in json.load(open(gn_path)) if c['country']=='FR']
A = {}
for c in gn:
    k = c['admin2'] + '|' + norm(c['name'])
    A.setdefault(k, [round(float(c['lat']),4), round(float(c['lng']),4)])
def dept_of(insee): return insee[:3] if insee.startswith('97') else insee[:2]
cps = json.load(open(cp_path))
dec = {c['code']: c for c in json.load(open(dec_path)) if c.get('type')=='commune-actuelle'}
# communes -> coords
com = {}
for insee, c in dec.items():
    k = dept_of(insee) + '|' + norm(c['nom'])
    if k in A: com[insee] = A[k]
PLM = {'751':'75056','6938':'69123','132':'13055'}
for r in cps:
    ci = r['codeCommune']
    for pre, parent in PLM.items():
        if ci.startswith(pre) and ci not in dec and parent in com: com[ci] = com[parent]
bycp = {}
for r in cps:
    bycp.setdefault(r['codePostal'], set()).add(r['codeCommune'])
B = {}
for cp, ins in bycp.items():
    pts = [com[i] for i in ins if i in com]
    if pts:
        # la commune la plus peuplée de ce code postal sert de repère
        best = max((i for i in ins if i in com), key=lambda i: dec.get(i,{}).get('population') or 0)
        B[cp] = com[best]
# codes postaux sans repère : le code postal le plus proche du même département (position approximative)
X = {}
known = sorted(B)
for cp in bycp:
    if cp in B: continue
    same = [k for k in known if k[:2] == cp[:2]]
    if same: X[cp] = B[min(same, key=lambda k: abs(int(k) - int(cp)) if k.isdigit() and cp.isdigit() else 99999)]
print('approx CP', len(X))
tot = sum((c.get('population') or 0) for c in dec.values())
cov_com = sum((c.get('population') or 0) for i,c in dec.items() if i in com)
cov_cp = 0
for insee, c in dec.items():
    if any(insee in bycp.get(cp,()) and cp in B for cp in c.get('codesPostaux',[])): cov_cp += c.get('population') or 0
print('communes:', len(dec), 'matched', len(com), f'pop {cov_com/tot:.1%}', '| CP:', len(bycp), 'with coords', len(B), f'pop via CP {cov_cp/tot:.1%}')
# toutes les communes par leur nom (sans code postal) : position propre, sinon celle de leur code postal
noms = {}
for insee, c in dec.items():
    pos = com.get(insee)
    if not pos:
        for cp in c.get('codesPostaux', []):
            if cp in B: pos = B[cp]; break
            if cp in X: pos = X[cp]; break
    if not pos: continue
    noms.setdefault(norm(c['nom']), []).append([round(pos[0],3), round(pos[1],3)])
print('noms de communes :', len(noms))
out = {'source':'GeoNames (CC BY 4.0) + codes postaux La Poste / Etalab', 'communes':{k:v for k,v in A.items()}, 'cp':B, 'cpApprox':X, 'noms':noms}
json.dump(out, open(out_path,'w'), separators=(',',':'), ensure_ascii=False)
