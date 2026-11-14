import json, sys, os, urllib.request, concurrent.futures as cf
OUT = sys.argv[1]
DEP = [("01","Amazonas",-6.23,-77.87),("02","Ancash",-9.53,-77.53),("03","Apurimac",-13.64,-72.88),("04","Arequipa",-16.40,-71.54),("05","Ayacucho",-13.16,-74.22),("06","Cajamarca",-7.16,-78.51),("07","Callao",-12.06,-77.13),("08","Cusco",-13.53,-71.97),("09","Huancavelica",-12.79,-74.97),("10","Huanuco",-9.93,-76.24),("11","Ica",-14.07,-75.73),("12","Junin",-12.07,-75.21),("13","La Libertad",-8.11,-79.03),("14","Lambayeque",-6.77,-79.84),("15","Lima",-12.05,-77.04),("16","Loreto",-3.75,-73.25),("17","Madre de Dios",-12.59,-69.19),("18","Moquegua",-17.19,-70.94),("19","Pasco",-10.68,-76.26),("20","Piura",-5.19,-80.63),("21","Puno",-15.84,-70.02),("22","San Martin",-6.03,-76.97),("23","Tacna",-18.01,-70.25),("24","Tumbes",-3.57,-80.45),("25","Ucayali",-8.38,-74.55)]
P = "PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M,QV2M,GWETROOT,GWETTOP"
def get(d):
    f = os.path.join(OUT, d[0]+".json")
    if os.path.exists(f): return d[0], "cached"
    u = f"https://power.larc.nasa.gov/api/temporal/monthly/point?parameters={P}&community=AG&longitude={d[3]}&latitude={d[2]}&start=2000&end=2024&format=JSON"
    with urllib.request.urlopen(u, timeout=120) as r: data = json.load(r)
    data["_dep"] = {"id":d[0],"name":d[1],"lat":d[2],"lon":d[3]}
    json.dump(data, open(f,"w"))
    return d[0], "ok"
with cf.ThreadPoolExecutor(4) as ex:
    for r in ex.map(get, DEP): print(*r)
