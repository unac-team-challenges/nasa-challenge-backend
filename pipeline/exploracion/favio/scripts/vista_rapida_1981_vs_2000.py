import json, os, sys, math, statistics as st
sys.path.insert(0, os.path.dirname(__file__))
from collections import Counter
D=sys.argv[1]
VARS={"PRECTOTCORR":("Lluvia","%/déc",365),"T2M":("Temp media","°C/déc",1),"T2M_MAX":("Temp máx","°C/déc",1),"T2M_MIN":("Temp mín","°C/déc",1),"RH2M":("Humedad rel.","pts/déc",1),"QV2M":("Humedad abs.","g/kg/déc",1),"GWETROOT":("Hum. suelo raíz","/déc",1),"GWETTOP":("Hum. suelo sup.","/déc",1)}
def mk(x):
    n=len(x); s=sum((x[j]>x[i])-(x[j]<x[i]) for i in range(n) for j in range(i+1,n))
    t=Counter(x); var=(n*(n-1)*(2*n+5)-sum(c*(c-1)*(2*c+5) for c in t.values()))/18
    z=0 if s==0 else (s-1 if s>0 else s+1)/math.sqrt(var); return 2*(1-0.5*(1+math.erf(abs(z)/math.sqrt(2))))
def sen(x): return st.median((x[j]-x[i])/(j-i) for i in range(len(x)) for j in range(i+1,len(x)))
def bh(ps):
    n=len(ps); o=sorted(range(n),key=lambda i:ps[i]); q=[0]*n; prev=1
    for r,i in reversed(list(enumerate(o,1))): prev=min(prev,ps[i]*n/r); q[i]=prev
    return q
deps=[json.load(open(os.path.join(D,f))) for f in sorted(os.listdir(D)) if f.endswith(".json")]
PER={"1981-2024":range(1981,2025),"2000-2024":range(2000,2025)}
out={}
for v,(lab,u,k) in VARS.items():
    out[v]={}
    for pn,yrs in PER.items():
        rows=[]
        for d in deps:
            x=[d["properties"]["parameter"][v][f"{y}13"]*k for y in yrs]
            miss=sum(1 for a in x if a<-900)
            if miss: rows.append((d["_dep"]["name"],None,miss)); continue
            m=st.mean(x); s=sen(x)*10
            if v=="PRECTOTCORR": s=100*s/m
            rows.append((d["_dep"]["name"],dict(slope=s,p=mk(x)),0))
        ok=[r for r in rows if r[1]]
        for r,q in zip(ok,bh([r[1]["p"] for r in ok])): r[1]["q"]=q
        out[v][pn]={r[0]:r[1] for r in ok}
        bad=[r[0] for r in rows if not r[1]]
        up=sum(r[1]["q"]<.05 and r[1]["slope"]>0 for r in ok); dn=sum(r[1]["q"]<.05 and r[1]["slope"]<0 for r in ok)
        out[v][pn+"_summary"]=(up,dn,bad)
print("RESUMEN (departamentos con cambio real tras BH: suben / bajan)")
print(f"{'Variable':18s} {'1981-2024':>12s} {'2000-2024':>12s}")
for v,(lab,u,k) in VARS.items():
    a=out[v]["1981-2024_summary"]; b=out[v]["2000-2024_summary"]
    print(f"{lab:18s} {a[0]:>5d} / {a[1]:<4d} {b[0]:>5d} / {b[1]:<4d} {'faltan:'+str(a[2]) if a[2] else ''}")
def f(r): 
    if not r: return "   s/d   "
    return f"{r['slope']:+7.2f}{'**' if r['q']<.05 else ('* ' if r['p']<.05 else '  ')}"
for v in ["PRECTOTCORR","T2M","T2M_MAX"]:
    lab,u,_=VARS[v]; print(f"\n{lab} ({u})   1981-2024 | 2000-2024")
    L=out[v]["1981-2024"]; C=out[v]["2000-2024"]
    for dep in sorted(L,key=lambda d:L[d]["slope"]):
        print(f"  {dep:14s} {f(L[dep])} | {f(C.get(dep))}")
json.dump({v:{p:out[v][p] for p in PER} for v in VARS},open(os.path.join(D,"..","trends_1981_vs_2000.json"),"w"),ensure_ascii=False,indent=1)
