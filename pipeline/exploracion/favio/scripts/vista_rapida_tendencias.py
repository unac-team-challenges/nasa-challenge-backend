import json, os, sys, math, statistics as st
D = sys.argv[1]
VARS = {"PRECTOTCORR":("Lluvia","mm/año",365),"T2M":("Temp media","°C",1),"T2M_MAX":("Temp máx","°C",1),"T2M_MIN":("Temp mín","°C",1),"RH2M":("Humedad rel.","%",1),"QV2M":("Humedad abs.","g/kg",1),"GWETROOT":("Humedad suelo raíz","0-1",1),"GWETTOP":("Humedad suelo sup.","0-1",1)}
def mk(x):
    n=len(x); s=sum((x[j]>x[i])-(x[j]<x[i]) for i in range(n) for j in range(i+1,n))
    # ties correction
    from collections import Counter
    t=Counter(x); var=(n*(n-1)*(2*n+5)-sum(c*(c-1)*(2*c+5) for c in t.values()))/18
    z=0 if s==0 else (s-1 if s>0 else s+1)/math.sqrt(var)
    p=2*(1-0.5*(1+math.erf(abs(z)/math.sqrt(2))))
    return z,p
def sen(x):
    return st.median((x[j]-x[i])/(j-i) for i in range(len(x)) for j in range(i+1,len(x)))
def lag1(x):
    m=st.mean(x); num=sum((x[i]-m)*(x[i+1]-m) for i in range(len(x)-1)); den=sum((v-m)**2 for v in x); return num/den
def bh(ps):
    n=len(ps); o=sorted(range(n),key=lambda i:ps[i]); q=[0]*n; prev=1
    for r,i in reversed(list(enumerate(o,1))): prev=min(prev,ps[i]*n/r); q[i]=prev
    return q
rows=[]
files=sorted(f for f in os.listdir(D) if f.endswith(".json"))
res={v:[] for v in VARS}
for f in files:
    d=json.load(open(os.path.join(D,f))); dep=d["_dep"]["name"]; P=d["properties"]["parameter"]
    for v,(lab,u,k) in VARS.items():
        x=[P[v][f"{y}13"]*k for y in range(2000,2025)]
        if any(val<-900 for val in x): res[v].append((dep,None)); continue
        z,p=mk(x); s=sen(x)*10
        res[v].append((dep,dict(mean=st.mean(x),slope=s,p=p,lag1=lag1(x))))
out={}
for v,(lab,u,k) in VARS.items():
    ok=[r for r in res[v] if r[1]]; q=bh([r[1]["p"] for r in ok])
    for r,qq in zip(ok,q): r[1]["q"]=qq
    up=sum(1 for r in ok if r[1]["q"]<0.05 and r[1]["slope"]>0); dn=sum(1 for r in ok if r[1]["q"]<0.05 and r[1]["slope"]<0)
    pu=sum(1 for r in ok if r[1]["p"]<0.05 and r[1]["slope"]>0); pd=sum(1 for r in ok if r[1]["p"]<0.05 and r[1]["slope"]<0)
    print(f"\n== {lab} ({u}, pendiente por década) | significativo tras BH: {up} suben, {dn} bajan | p<0.05 sin corregir: {pu} suben, {pd} bajan")
    for dep,r in sorted(ok,key=lambda r:r[1]["slope"]):
        rel = f" ({100*r['slope']/r['mean']:+.0f}%/déc)" if v=="PRECTOTCORR" and r["mean"]>0 else ""
        flag="**" if r["q"]<0.05 else ("*" if r["p"]<0.05 else "")
        print(f"  {dep:14s} media {r['mean']:8.2f}  pend {r['slope']:+8.3f}{rel:12s} p={r['p']:.3f} q={r['q']:.3f} lag1={r['lag1']:+.2f} {flag}")
    out[v]={dep:r for dep,r in ok}
json.dump(out,open(os.path.join(D,"..","trends_power.json"),"w"),ensure_ascii=False,indent=1)
