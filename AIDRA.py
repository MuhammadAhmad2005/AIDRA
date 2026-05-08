"""
AIDRA — Adaptive Intelligent Disaster Response Agent
========================================================
AIC-201 | Dr. Arshad Farhad | Semester 5-A

"""

import tkinter as tk
from tkinter import ttk, messagebox
import math, random, time, threading, collections, csv, os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  PALETTE
# ═══════════════════════════════════════════════════════════════
BG           = "#0d1117"
ROAD_MAIN    = "#1e2433"
SIDEWALK_C   = "#1a2030"
BLOCK_BG     = "#161c29"
CARD_BORDER  = "#1e2840"

FIRE_A       = "#ff6600"; FIRE_B="#ff3300"; FIRE_C="#ff9933"; FIRE_D="#ffee44"

BLOCKED_C    = "#cc2222"
VICTIM_CRIT  = "#ff4444"; VICTIM_MOD="#ffaa00"; VICTIM_MIN="#44dd88"
BASE_C       = "#3377ff"; HOSP_C="#ff2244"
AMB_C        = "#ffffff"; SIREN_R="#ff3333"; SIREN_B="#3399ff"

ROUTE_FAST   = "#00ccff"; ROUTE_SAFE="#00ff88"
EXPLORE_C    = "#2255aa"
FRONTIER_C   = "#ccaa00"
PATH_FINAL   = "#00ff44"

PANEL_BG     = "#0a0e16"
CARD_BG      = "#111620"
ACCENT       = "#4d9fff"
TEXT         = "#c8d6f0"
DIM          = "#6070a0"
OK_C         = "#33cc77"; WARN_C="#ffaa44"; DANGER_C="#ff4455"
PURPLE       = "#aa77ff"; TEAL="#00ddcc"

# ═══════════════════════════════════════════════════════════════
#  MAP CONSTANTS
# ═══════════════════════════════════════════════════════════════
GRID_ROWS    = 9
GRID_COLS    = 13
CELL         = 74
MAP_PAD_X    = 6
MAP_PAD_Y    = 6

RESCUE_BASE  = (4, 4)
HOSPITALS    = [(1,11),(4,11)]
FIRE_ZONES   = {(0,2),(1,2),(2,1),(0,6),(0,7),(2,8),(3,8),
                (6,1),(7,2),(7,8),(8,7),(6,10),(5,10)}
BLOCKED_INIT = {(2,4),(2,5),(2,6),(2,7),(3,10),(4,9)}

VICTIMS_INIT = [
    {"id":1,"pos":(0,3),"severity":"critical","urgency":5,"health":28,"kits":2},
    {"id":2,"pos":(2,2),"severity":"critical","urgency":5,"health":22,"kits":2},
    {"id":3,"pos":(3,7),"severity":"moderate","urgency":3,"health":58,"kits":1},
    {"id":4,"pos":(5,6),"severity":"moderate","urgency":3,"health":62,"kits":1},
    {"id":5,"pos":(6,9),"severity":"minor",   "urgency":1,"health":82,"kits":1},
]

# FIX-1: cap maximum spawned victims to prevent infinite loop
MAX_TOTAL_VICTIMS = 8

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "aidra_survival_data.csv")

# ═══════════════════════════════════════════════════════════════
#  SECTION 1 – ENVIRONMENT MODEL
# ═══════════════════════════════════════════════════════════════
class GridMap:
    def __init__(self):
        self.fire    = set(FIRE_ZONES)
        self.blocked = set(BLOCKED_INIT)

    def passable(self,r,c):
        return 0<=r<GRID_ROWS and 0<=c<GRID_COLS and (r,c) not in self.blocked

    def cost(self,r,c):  return 5 if (r,c) in self.fire else 1
    def risk(self,r,c):
        if (r,c) in self.fire:    return 0.9
        if (r,c) in self.blocked: return 1.0
        return 0.05

    def neighbours(self,r,c):
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr,nc=r+dr,c+dc
            if self.passable(nr,nc): yield nr,nc

    def block_road(self,cell): self.blocked.add(cell)

    def spread_fire(self):
        new=set()
        for (r,c) in list(self.fire):
            for nr,nc in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if 0<=nr<GRID_ROWS and 0<=nc<GRID_COLS and random.random()<0.08:
                    if (nr,nc) not in self.blocked: new.add((nr,nc))
        self.fire|=new; return new

# ═══════════════════════════════════════════════════════════════
#  SECTION 2 – SEARCH ALGORITHMS  (with expansion trace)
# ═══════════════════════════════════════════════════════════════
def heuristic(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])

def bfs(grid, start, goal, trace_cb=None):
    frontier=collections.deque([(start,)]); visited={start}; ne=0
    while frontier:
        path=frontier.popleft(); node=path[-1]; ne+=1
        if trace_cb: trace_cb(node, "explore", ne)
        if node==goal:
            return path,ne,sum(grid.cost(*c) for c in path)
        for nb in grid.neighbours(*node):
            if nb not in visited:
                visited.add(nb)
                if trace_cb: trace_cb(nb,"frontier",ne)
                frontier.append(path+(nb,))
    return None,ne,float('inf')

def dfs(grid, start, goal, trace_cb=None):
    frontier=[(start,)]; visited={start}; ne=0
    while frontier:
        path=frontier.pop(); node=path[-1]; ne+=1
        if trace_cb: trace_cb(node,"explore",ne)
        if node==goal:
            return path,ne,sum(grid.cost(*c) for c in path)
        for nb in grid.neighbours(*node):
            if nb not in visited:
                visited.add(nb)
                if trace_cb: trace_cb(nb,"frontier",ne)
                frontier.append(path+(nb,))
    return None,ne,float('inf')

def greedy(grid, start, goal, trace_cb=None):
    import heapq
    frontier=[(heuristic(start,goal),start,(start,))]; visited={start}; ne=0
    while frontier:
        _,node,path=heapq.heappop(frontier); ne+=1
        if trace_cb: trace_cb(node,"explore",ne)
        if node==goal:
            return path,ne,sum(grid.cost(*c) for c in path)
        for nb in grid.neighbours(*node):
            if nb not in visited:
                visited.add(nb)
                if trace_cb: trace_cb(nb,"frontier",ne)
                heapq.heappush(frontier,(heuristic(nb,goal),nb,path+(nb,)))
    return None,ne,float('inf')

def astar(grid, start, goal, trace_cb=None):
    import heapq
    frontier=[(heuristic(start,goal),0,start,(start,))]; g={start:0}; ne=0
    while frontier:
        _,gc,node,path=heapq.heappop(frontier); ne+=1
        if trace_cb: trace_cb(node,"explore",ne)
        if node==goal: return path,ne,gc
        for nb in grid.neighbours(*node):
            ng=gc+grid.cost(*nb)
            if ng<g.get(nb,float('inf')):
                g[nb]=ng
                if trace_cb: trace_cb(nb,"frontier",ne)
                heapq.heappush(frontier,(ng+heuristic(nb,goal),ng,nb,path+(nb,)))
    return None,ne,float('inf')

def astar_safe(grid, start, goal):
    import heapq
    def rc(r,c): return 12 if (r,c) in grid.fire else 1
    frontier=[(heuristic(start,goal),0,start,(start,))]; g={start:0}; ne=0
    while frontier:
        _,gc,node,path=heapq.heappop(frontier); ne+=1
        if node==goal: return path,ne,gc
        for nb in grid.neighbours(*node):
            ng=gc+rc(*nb)
            if ng<g.get(nb,float('inf')):
                g[nb]=ng
                heapq.heappush(frontier,(ng+heuristic(nb,goal),ng,nb,path+(nb,)))
    return None,ne,float('inf')

def route_risk(grid,path):
    if not path: return 1.0
    return round(sum(1 for r,c in path if (r,c) in grid.fire)/max(len(path),1),3)

# ═══════════════════════════════════════════════════════════════
#  SECTION 3 – SIMULATED ANNEALING
# ═══════════════════════════════════════════════════════════════
def simulated_annealing(victims, grid, base):
    def tour(order):
        pos=base; total=0
        for v in order:
            _,_,c=astar(grid,pos,v["pos"]); total+=c; pos=v["pos"]
        return total
    cur=list(victims); random.shuffle(cur)
    best=cur[:]; bc=tour(best); cc=bc; T=80.0; iters=0
    while T>0.8:
        i,j=random.sample(range(len(cur)),2); cur[i],cur[j]=cur[j],cur[i]
        nc=tour(cur)
        if nc<cc or random.random()<math.exp(-(nc-cc)/T):
            cc=nc
            if cc<bc: bc=cc; best=cur[:]
        else: cur[i],cur[j]=cur[j],cur[i]
        T*=0.93; iters+=1
    return best,bc,iters

# ═══════════════════════════════════════════════════════════════
#  SECTION 4 – CSP
# ═══════════════════════════════════════════════════════════════
class CSPSolver:
    def __init__(self,victims,n_amb=2,total_kits=10):
        self.victims=victims; self.n_amb=n_amb; self.total_kits=total_kits; self.bt=0

    def solve(self,use_h=True):
        self.bt=0; remaining=list(self.victims); trips=[]
        while remaining:
            batch=remaining[:4]; domains={v["id"]:list(range(self.n_amb)) for v in batch}
            res=self._bt({},domains,batch,use_h)
            if res:
                trips.append(res); remaining=[v for v in remaining if v["id"] not in res]
            else:
                for v in remaining: trips.append({v["id"]:0}); break
        flat={}
        for t in trips: flat.update(t)
        return flat,self.bt

    def _bt(self,asgn,doms,batch,use_h):
        if len(asgn)==len(batch): return asgn.copy()
        una=[v for v in batch if v["id"] not in asgn]
        var=min(una,key=lambda v:len(doms[v["id"]])) if use_h else una[0]
        for amb in doms[var["id"]]:
            if self._ok(asgn,var["id"],amb):
                asgn[var["id"]]=amb
                saved={v["id"]:doms[v["id"]][:] for v in batch}
                if use_h: self._fc(asgn,doms)
                res=self._bt(asgn,doms,batch,use_h)
                if res is not None: return res
                del asgn[var["id"]]
                for v in batch: doms[v["id"]]=saved[v["id"]]
                self.bt+=1
        return None

    def _ok(self,asgn,vid,amb):
        if sum(1 for a in asgn.values() if a==amb)>=2: return False
        used=sum(v["kits"] for v in self.victims if v["id"] in asgn)
        this=next((v["kits"] for v in self.victims if v["id"]==vid),0)
        return used+this<=self.total_kits

    def _fc(self,asgn,doms):
        full={a for a in range(self.n_amb) if sum(1 for x in asgn.values() if x==a)>=2}
        for vid in list(doms):
            if vid not in asgn: doms[vid]=[a for a in doms[vid] if a not in full]

# ═══════════════════════════════════════════════════════════════
#  SECTION 5 – ML  (kNN + NaiveBayes + Decision Tree)  E7
# ═══════════════════════════════════════════════════════════════
class KNN:
    def __init__(self,k=3): self.k=k; self.X=[]; self.y=[]
    def fit(self,X,y): self.X=X; self.y=y
    def _d(self,a,b): return math.sqrt(sum((x-z)**2 for x,z in zip(a,b)))
    def predict(self,x):
        d=sorted([(self._d(x,xi),yi) for xi,yi in zip(self.X,self.y)])
        top=[t[1] for t in d[:self.k]]; return max(set(top),key=top.count)
    def proba(self,x):
        d=sorted([(self._d(x,xi),yi) for xi,yi in zip(self.X,self.y)])
        return [t[1] for t in d[:self.k]].count(1)/self.k

class NaiveBayes:
    def fit(self,X,y):
        self.cls=list(set(y)); self.pri={}; self.mu={}; self.sg={}
        for c in self.cls:
            Xc=[X[i] for i in range(len(X)) if y[i]==c]
            self.pri[c]=len(Xc)/len(X)
            self.mu[c]=[sum(col)/len(col) for col in zip(*Xc)]
            self.sg[c]=[math.sqrt(sum((v-m)**2 for v in col)/max(len(col)-1,1))+1e-9
                        for col,m in zip(zip(*Xc),self.mu[c])]
    def _g(self,x,m,s):
        return (1/(s*math.sqrt(2*math.pi)))*math.exp(-0.5*((x-m)/s)**2)
    def predict(self,x):
        sc={c:math.log(self.pri[c]+1e-9)+sum(math.log(self._g(xi,m,s)+1e-9)
           for xi,m,s in zip(x,self.mu[c],self.sg[c])) for c in self.cls}
        return max(sc,key=sc.get)
    def proba(self,x):
        sc={c:math.log(self.pri[c]+1e-9)+sum(math.log(self._g(xi,m,s)+1e-9)
           for xi,m,s in zip(x,self.mu[c],self.sg[c])) for c in self.cls}
        tot=sum(math.exp(v) for v in sc.values())
        return math.exp(sc.get(1,sc[self.cls[0]]))/max(tot,1e-9)

class DecisionTree:
    """Simple CART-like decision tree (depth-limited, from scratch)."""
    def __init__(self,max_depth=5): self.max_depth=max_depth; self.tree=None

    def fit(self,X,y): self.tree=self._build(X,y,0)

    def _gini(self,y):
        n=len(y)
        if n==0: return 0
        p=sum(1 for yi in y if yi==1)/n; return 1-p**2-(1-p)**2

    # FIX-2: _split now returns a consistent sentinel and correct tuple
    def _split(self,X,y):
        best_g=float('inf')
        best=(None,None,None,None,None,None,None)  # sentinel with None fi
        for fi in range(len(X[0])):
            vals=sorted(set(x[fi] for x in X))
            for thr in [(vals[i]+vals[i+1])/2 for i in range(len(vals)-1)]:
                Xl=[X[i] for i in range(len(X)) if X[i][fi]<=thr]
                yl=[y[i] for i in range(len(y)) if X[i][fi]<=thr]
                Xr=[X[i] for i in range(len(X)) if X[i][fi]>thr]
                yr=[y[i] for i in range(len(y)) if X[i][fi]>thr]
                g=(len(yl)*self._gini(yl)+len(yr)*self._gini(yr))/max(len(y),1)
                if g<best_g:
                    best_g=g
                    best=(g,fi,thr,Xl,Xr,yl,yr)
        return best

    def _build(self,X,y,depth):
        if not y: return {"leaf":0}
        if depth>=self.max_depth or len(set(y))==1:
            return {"leaf":round(sum(y)/max(len(y),1))}
        best=self._split(X,y)
        # FIX-2: check best[1] (fi) for None, not best[3] (Xl list)
        if best[1] is None:
            return {"leaf":round(sum(y)/max(len(y),1))}
        _,fi,thr,Xl,Xr,yl,yr=best
        return {"fi":fi,"thr":thr,
                "left":self._build(Xl,yl,depth+1),
                "right":self._build(Xr,yr,depth+1)}

    def _walk(self,node,x):
        if "leaf" in node: return node["leaf"]
        return self._walk(node["left"],x) if x[node["fi"]]<=node["thr"] \
               else self._walk(node["right"],x)

    def predict(self,x): return self._walk(self.tree,x)
    def proba(self,x): return float(self._walk(self.tree,x))

# ─── E3: CSV dataset ─────────────────────────────────────────
def generate_csv_dataset(path):
    random.seed(42)
    with open(path,"w",newline="") as f:
        w=csv.writer(f)
        w.writerow(["health","urgency","distance","risk","survived"])
        for _ in range(300):
            h=random.uniform(5,100); u=random.randint(1,5)
            d=random.uniform(0,25);  r=random.uniform(0,1)
            s=h/100-d/35-r*0.3-(u/5)*0.15
            w.writerow([round(h,2),u,round(d,2),round(r,3),1 if s>0.15 else 0])

def load_csv_dataset(path):
    X=[]; y=[]
    with open(path,"r") as f:
        rd=csv.DictReader(f)
        for row in rd:
            X.append([float(row["health"]),float(row["urgency"]),
                      float(row["distance"]),float(row["risk"])])
            y.append(int(row["survived"]))
    return X,y

def train_models():
    if not os.path.exists(CSV_PATH): generate_csv_dataset(CSV_PATH)
    X,y=load_csv_dataset(CSV_PATH)
    random.seed(7); idx=list(range(len(X))); random.shuffle(idx)
    sp=int(0.8*len(idx))
    Xtr=[X[i] for i in idx[:sp]]; ytr=[y[i] for i in idx[:sp]]
    Xte=[X[i] for i in idx[sp:]]; yte=[y[i] for i in idx[sp:]]

    knn=KNN(3);      knn.fit(Xtr,ytr)
    nb=NaiveBayes(); nb.fit(Xtr,ytr)
    dt=DecisionTree(max_depth=5); dt.fit(Xtr,ytr)

    def met(m,Xt,yt):
        pr=[m.predict(x) for x in Xt]
        tp=tn=fp=fn=0
        for p,t in zip(pr,yt):
            if   p==1 and t==1: tp+=1
            elif p==0 and t==0: tn+=1
            elif p==1 and t==0: fp+=1
            else:               fn+=1
        acc=(tp+tn)/max(len(yt),1); prec=tp/max(tp+fp,1)
        rec=tp/max(tp+fn,1); f1=2*prec*rec/max(prec+rec,1e-9)
        return {"acc":acc,"prec":prec,"rec":rec,"f1":f1,"cm":[[tp,fp],[fn,tn]]}
    return knn,nb,dt,met(knn,Xte,yte),met(nb,Xte,yte),met(dt,Xte,yte)

# ═══════════════════════════════════════════════════════════════
#  SECTION 6 – FUZZY LOGIC  (E4: returns membership values)
# ═══════════════════════════════════════════════════════════════
class FuzzyRouter:
    def decide(self,hazard,dist_ratio,urgency):
        n=(urgency-1)/4
        h_low=max(0,min(1,(0.3-hazard)/0.3))
        h_med=max(0,1-abs(hazard-0.5)/0.25)
        h_hi =max(0,min(1,(hazard-0.6)/0.3))
        u_lo =max(0,1-n/0.4)
        u_hi =max(0,(n-0.5)/0.4)
        d_ok =max(0,min(1,(2.0-dist_ratio)/1.2))
        d_lng=max(0,min(1,(dist_ratio-1.5)/1.0))
        r1=min(h_hi,u_lo); r2=min(h_hi,d_ok)
        r3=h_low;           r4=min(d_lng,u_hi)
        r5=h_med*0.5
        safe_w=r1*0.7+r2*1.0+r5*0.5; fast_w=r3*1.0+r4*0.9
        tot=safe_w+fast_w
        if tot<1e-9:
            reason="Neutral"
            score=0.5
        else:
            score=safe_w/tot
            if   score>0.55: reason="SAFE route (high hazard)"
            elif score<0.40: reason="FAST route (low hazard, urgency high)"
            else:            reason="BORDERLINE → defaulting SAFE"
        memberships={
            "hazard_low":round(h_low,3),"hazard_med":round(h_med,3),
            "hazard_hi":round(h_hi,3),"urgency_lo":round(u_lo,3),
            "urgency_hi":round(u_hi,3),"dist_ok":round(d_ok,3),
            "dist_long":round(d_lng,3),"safe_weight":round(safe_w,3),
            "fast_weight":round(fast_w,3),"score":round(score,3)
        }
        return score, reason, memberships

# ═══════════════════════════════════════════════════════════════
#  SECTION 7 – AGENT
# ═══════════════════════════════════════════════════════════════
class Agent:
    def __init__(self,log_cb=None,kpi_cb=None,map_cb=None,
                 fuzzy_cb=None,expand_cb=None):
        self.grid     = GridMap()
        self.victims  = [dict(v) for v in VICTIMS_INIT]
        self.base     = RESCUE_BASE
        self.hospitals= HOSPITALS
        self.res      = {"ambulances":2,"team":1,"kits":10}
        self.rescued  = []
        self.running  = False
        self.algo     = "A*"
        self.delay    = 0.25
        self.show_expansion = True

        self.log_cb   = log_cb    or (lambda m,s:None)
        self.kpi_cb   = kpi_cb    or (lambda d:None)
        self.map_cb   = map_cb    or (lambda *a:None)
        self.fuzzy_cb = fuzzy_cb  or (lambda d:None)
        self.expand_cb= expand_cb or (lambda *a:None)

        self.knn,self.nb,self.dt,self.km,self.nm,self.dm = train_models()
        self.fuzzy    = FuzzyRouter()
        self.kpis     = {"saved":0,"times":[],"risks":[],"costs":[]}
        self.report   = []

        self.algo_runtimes = {}

    def log(self,m,s="info"):
        ts=datetime.now().strftime("%H:%M:%S")
        self.log_cb(f"[{ts}]  {m}",s)

    # FIX-3: renamed inner variable to 'algo_fn' to avoid shadowing
    def _algo_fn(self):
        return {"A*":astar,"BFS":bfs,"DFS":dfs,"Greedy":greedy}.get(self.algo,astar)

    def _make_trace(self):
        if not self.show_expansion: return None
        def cb(node,kind,step):
            self.expand_cb(node,kind,step)
            time.sleep(max(0.015, self.delay*0.08))
        return cb

    def select_route(self,start,goal,urgency):
        # FIX-3: use algo_fn variable, not fn (which is a param name in outer scope)
        algo_fn=self._algo_fn()
        trace=self._make_trace()
        fp,fn_e,fc=algo_fn(self.grid,start,goal,trace)
        sp,sn_e,sc=astar_safe(self.grid,start,goal)
        if not fp and not sp: return None,0,float('inf'),0,"no path",{}
        fr=route_risk(self.grid,fp) if fp else 1.0
        dr=sc/max(fc,1) if fp else 1.0
        score,reason,memb=self.fuzzy.decide(fr,dr,urgency)
        self.fuzzy_cb({"hazard":fr,"dist_ratio":dr,"urgency":urgency,**memb,"reason":reason})
        nodes=(fn_e or 0)+(sn_e or 0)
        if score>=0.5:
            chosen=sp or fp; cr=route_risk(self.grid,chosen); cc=sc if sp else fc
            return chosen,cr,cc,nodes,f"[SAFE] {reason}",memb
        else:
            chosen=fp or sp; cr=fr; cc=fc if fp else sc
            return chosen,cr,cc,nodes,f"[FAST] {reason}",memb

    def predict_survival(self,v,delay,risk):
        f=[v["health"],v["urgency"],delay,risk]
        kp=self.knn.proba(f); np_=self.nb.proba(f); dp=self.dt.proba(f)
        return round((kp+np_+dp)/3,3)

    def prioritise(self):
        rem=[v for v in self.victims if v.get("status")!="rescued"]
        scored=[]
        for v in rem:
            d=heuristic(self.base,v["pos"])
            r=0.6 if v["pos"] in self.grid.fire else 0.1
            s=self.predict_survival(v,d,r)
            sc=v["urgency"]*3+(100-v["health"])/10+(1-s)*5
            scored.append((sc,v))
        scored.sort(key=lambda t:-t[0])
        return [v for _,v in scored]

    def allocate(self):
        rem=[v for v in self.victims if v.get("status")!="rescued"]
        csp=CSPSolver(rem,self.res["ambulances"],self.res["kits"])
        wh,bth=csp.solve(True)
        csp2=CSPSolver(rem,self.res["ambulances"],self.res["kits"])
        _,btn=csp2.solve(False)
        self.log(f"CSP  MRV BT={bth}  plain BT={btn}  saved={max(0,btn-bth)}","csp")
        return wh

    # FIX-4: renamed loop variable to 'search_name' and 'search_fn' to avoid collision
    def compare_algos(self,victim):
        if not victim: return
        self.log("─── Algorithm Comparison ───────────────","head")
        best_cost=float('inf'); results={}
        for search_name,search_fn in [("BFS",bfs),("DFS",dfs),("Greedy",greedy),("A*",astar)]:
            t0=time.perf_counter()
            p,ne,c=search_fn(self.grid,self.base,victim["pos"])
            rt=round((time.perf_counter()-t0)*1000,2)
            results[search_name]=(ne,c,rt)
            self.algo_runtimes[search_name]=rt
            self.log(f"  {search_name:7s} nodes={ne:3d}  cost={c:.1f}  time={rt}ms","compare")
            if c<best_cost: best_cost=c
        for search_name,(ne,c,rt) in results.items():
            por=round(c/max(best_cost,1),2) if c<float('inf') else "inf"
            self.log(f"  {search_name:7s} optimality ratio = {por}","compare")

    # E2 — dynamic new victim event (FIX-1: respect MAX cap)
    def _spawn_victim(self):
        if len(self.victims)>=MAX_TOTAL_VICTIMS:
            self.log(f"  (victim cap reached, no new spawn)","info")
            return None
        used_pos={v["pos"] for v in self.victims}
        for _ in range(30):
            r,c=random.randint(0,GRID_ROWS-1),random.randint(0,GRID_COLS-1)
            pos=(r,c)
            if pos not in used_pos and pos not in self.grid.fire \
               and pos not in self.grid.blocked and pos!=self.base:
                new_id=max(v["id"] for v in self.victims)+1
                sev=random.choice(["critical","moderate","minor"])
                urg={"critical":5,"moderate":3,"minor":1}[sev]
                hp={"critical":random.randint(15,40),
                    "moderate":random.randint(45,70),
                    "minor":random.randint(70,95)}[sev]
                nv={"id":new_id,"pos":pos,"severity":sev,
                    "urgency":urg,"health":hp,"kits":1}
                self.victims.append(nv)
                self.log(f"⚠ EVENT  NEW VICTIM V{new_id} ({sev.upper()}) at {pos}!","warn")
                self.map_cb("update",None,0,0)
                return nv
        return None

    def _event(self):
        ev=random.choice(["block","fire","kits","new_victim"])
        if ev=="block":
            r,c=random.randint(0,GRID_ROWS-1),random.randint(0,GRID_COLS-1)
            if (r,c) not in self.grid.fire and (r,c)!=self.base:
                self.grid.block_road((r,c))
                self.log(f"⚠ EVENT  Road blocked ({r},{c}) — replanning","warn")
                self._replan(f"road blocked at ({r},{c})")
                self.map_cb("update",None,0,0)
        elif ev=="fire":
            new=self.grid.spread_fire()
            if new:
                self.log(f"⚠ EVENT  Fire spread → {len(new)} cells","warn")
                self.map_cb("update",None,0,0)
        elif ev=="kits":
            if self.res["kits"]>1:
                self.res["kits"]-=1
                self.log(f"⚠ EVENT  Kit depleted — {self.res['kits']} remaining","warn")
        else:
            self._spawn_victim()

    def _replan(self,reason):
        order=self.prioritise()
        self.log(f"  ↺ REPLANNING ({reason})","warn")
        self.log("  New priority: "+", ".join(f"V{v['id']}" for v in order),"warn")

    # FIX-5 & FIX-6: robust run loop with proper termination
    def run(self):
        self.running=True; t0=time.time()
        self.log("══════ AIDRA MISSION STARTED ══════","head")
        alloc=self.allocate()
        if alloc:
            for vid,amb in alloc.items():
                self.log(f"  CSP → Victim {vid} → Ambulance {amb+1}","csp")

        order=self.prioritise()
        self.log("Priority: "+", ".join(f"V{v['id']}({v['severity']})" for v in order),"info")
        self.compare_algos(order[0] if order else None)
        if order:
            sa_ord,sa_c,sa_i=simulated_annealing(order,self.grid,self.base)
            self.log(f"SA tour cost={sa_c:.1f} in {sa_i} iters  order={[v['id'] for v in sa_ord]}","sa")

        amb_pos=[self.base,self.base]
        processed=set()  # victim IDs already dispatched

        # FIX-5: loop exits when no unprocessed victims remain, regardless of spawns
        while self.running:
            # Get victims not yet processed
            rem=[v for v in self.victims
                 if v.get("status")!="rescued" and v["id"] not in processed]
            if not rem:
                break  # all current victims handled — done

            order=self.prioritise()
            victim=next((v for v in order
                         if v["id"] not in processed and v.get("status")!="rescued"),None)
            if not victim:
                break

            processed.add(victim["id"])

            alloc=self.allocate()
            aid=alloc.get(victim["id"],0) if alloc else 0
            self.log(f"──── Amb-{aid+1} → V{victim['id']} ({victim['severity'].upper()}) ────","head")

            path,risk,cost,nodes,reason,_=self.select_route(
                amb_pos[aid],victim["pos"],victim["urgency"])
            if not path:
                self.log(f"  ✗ No path to V{victim['id']}","danger")
                self._replan("path blocked"); continue

            self.log(f"  Route [{self.algo}]  nodes={nodes}  cost={cost:.1f}  risk={risk:.2f}","route")
            self.log(f"  Fuzzy → {reason}","fuzzy")
            surv=self.predict_survival(victim,cost,risk)
            self.log(f"  ML survival est. V{victim['id']} = {surv:.1%} (kNN+NB+DT ensemble)","ml")

            self.expand_cb(None,"path",path)
            self.map_cb("route",path,aid,risk)
            self._walk(path,aid)
            amb_pos[aid]=victim["pos"]

            hosp=min(self.hospitals,key=lambda h:heuristic(victim["pos"],h))
            hp,hr,hc,_,hr2,_=self.select_route(victim["pos"],hosp,victim["urgency"])
            if hp:
                self.log(f"  Delivering → Hospital {hosp}  {hr2}","route")
                self.expand_cb(None,"path",hp)
                self.map_cb("route",hp,aid,hr)
                self._walk(hp,aid)
            amb_pos[aid]=hosp

            victim["status"]="rescued"
            rt=round(time.time()-t0,1)
            self.rescued.append(victim)
            self.kpis["saved"]+=1
            self.kpis["times"].append(rt)
            self.kpis["risks"].append(risk)
            self.kpis["costs"].append(cost)
            kits=min(victim["kits"],self.res["kits"])
            self.res["kits"]-=kits
            self.log(f"  ✓ V{victim['id']} RESCUED  t={rt}s  kits={self.res['kits']}","ok")

            self.report.append({
                "victim_id":victim["id"],"severity":victim["severity"],
                "rescue_time_s":rt,"route_risk":risk,"path_cost":cost,
                "route_type":"SAFE" if "SAFE" in reason else "FAST",
                "survival_est":surv,"kits_remaining":self.res["kits"]
            })

            self.map_cb("rescued",victim,aid,0)
            self.kpi_cb(self._get_kpis())

            # Trigger random events (capped by victim limit)
            if random.random()<0.45:
                self._event()

        self.log("══════ MISSION COMPLETE ══════","head")
        total=len(set(v["id"] for v in self.victims))
        self.log(f"  Saved {self.kpis['saved']}/{total}","ok")
        if self.kpis["times"]:
            avg=sum(self.kpis["times"])/len(self.kpis["times"])
            self.log(f"  Avg rescue time = {avg:.1f}s","ok")
        self.running=False
        self.kpi_cb(self._get_kpis())
        self._export_report()

    def _walk(self,path,aid):
        for pos in path:
            if not self.running: break
            self.map_cb("move",pos,aid,0)
            time.sleep(self.delay)

    def _get_kpis(self):
        t=self.kpis["times"]; r=self.kpis["risks"]; c=self.kpis["costs"]
        total=len(set(v["id"] for v in self.victims))
        return {"saved":self.kpis["saved"],"total":total,
                "avg_time":round(sum(t)/max(len(t),1),1),
                "risk":round(sum(r)/max(len(r),1),3),
                "por":round(sum(x/max(x,1) for x in c)/max(len(c),1),3),
                "util":round(self.kpis["saved"]/max(total,1)*100,1),
                "kits":self.res["kits"],
                "knn":self.km,"nb":self.nm,"dt":self.dm,
                "runtimes":self.algo_runtimes}

    def _export_report(self):
        if not self.report: return
        out=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "aidra_performance_report.csv")
        with open(out,"w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=self.report[0].keys())
            w.writeheader(); w.writerows(self.report)
        self.log(f"  📊 Report exported → {os.path.basename(out)}","ok")

# ═══════════════════════════════════════════════════════════════
#  SECTION 8 – GUI
# ═══════════════════════════════════════════════════════════════
class AIDRA_GUI:
    def __init__(self,root):
        self.root=root
        root.title("AIDRA v4 — Intelligent Disaster Response Agent  |  AIC-201")
        root.configure(bg=BG)
        root.geometry("1540x920")
        root.resizable(True,True)

        self.agent      = None
        self.amb_pos    = {0:RESCUE_BASE,1:RESCUE_BASE}
        self.route_items= []
        self.expand_items=[]
        self.fire_phase = 0
        self.siren_phase= 0
        self.tick       = 0
        self.show_exp_var= tk.BooleanVar(value=True)

        self.algo_var   = tk.StringVar(value="A*")
        self.speed_var  = tk.DoubleVar(value=0.25)

        self._build_ui()
        self._draw_city()
        self._animate()

    def _cx(self,c): return MAP_PAD_X+c*CELL+CELL//2
    def _cy(self,r): return MAP_PAD_Y+r*CELL+CELL//2
    def _tl(self,r,c): return MAP_PAD_X+c*CELL, MAP_PAD_Y+r*CELL

    def _build_ui(self):
        hdr=tk.Frame(self.root,bg="#060a10",height=50)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr,text="⬡  AIDRA v4  ·  ADAPTIVE INTELLIGENT DISASTER RESPONSE AGENT",
                 bg="#060a10",fg=ACCENT,font=("Consolas",13,"bold")).pack(side="left",padx=18,pady=12)
        self.clock_lbl=tk.Label(hdr,text="",bg="#060a10",fg=DIM,font=("Consolas",10))
        self.clock_lbl.pack(side="right",padx=18)
        tk.Label(hdr,text="AIC-201  ·  Dr. Arshad Farhad",
                 bg="#060a10",fg=DIM,font=("Consolas",10)).pack(side="right",padx=8)

        body=tk.Frame(self.root,bg=BG); body.pack(fill="both",expand=True)

        left=tk.Frame(body,bg=PANEL_BG,width=268)
        left.pack(side="left",fill="y"); left.pack_propagate(False)
        self._build_left(left)

        center=tk.Frame(body,bg=BG)
        center.pack(side="left",fill="both",expand=True)
        self._build_map(center)

        right=tk.Frame(body,bg=PANEL_BG,width=328)
        right.pack(side="right",fill="y"); right.pack_propagate(False)
        self._build_right(right)

    def _sec(self,p,title):
        tk.Label(p,text=title,bg=PANEL_BG,fg=ACCENT,
                 font=("Consolas",9,"bold")).pack(pady=(10,3),padx=14,anchor="w")
        tk.Frame(p,bg=CARD_BORDER,height=1).pack(fill="x",padx=14)

    def _build_left(self,p):
        self._sec(p,"CONTROLS")
        cf=tk.Frame(p,bg=PANEL_BG); cf.pack(fill="x",padx=14,pady=(8,2))
        tk.Label(cf,text="Algorithm",bg=PANEL_BG,fg=DIM,font=("Consolas",9)).pack(side="left")
        ttk.Combobox(cf,textvariable=self.algo_var,values=["A*","BFS","DFS","Greedy"],
                     width=9,state="readonly",font=("Consolas",9)).pack(side="right")

        sf=tk.Frame(p,bg=PANEL_BG); sf.pack(fill="x",padx=14,pady=2)
        tk.Label(sf,text="Delay",bg=PANEL_BG,fg=DIM,font=("Consolas",9)).pack(side="left")
        tk.Scale(sf,variable=self.speed_var,from_=0.05,to=1.0,resolution=0.05,
                 orient="horizontal",bg=PANEL_BG,fg=TEXT,troughcolor=CARD_BG,
                 highlightthickness=0,length=140,command=self._on_speed).pack(side="right")

        ef=tk.Frame(p,bg=PANEL_BG); ef.pack(fill="x",padx=14,pady=2)
        tk.Checkbutton(ef,text="Show search expansion",variable=self.show_exp_var,
                       bg=PANEL_BG,fg=DIM,selectcolor=CARD_BG,
                       font=("Consolas",8),activebackground=PANEL_BG).pack(side="left")

        bf=tk.Frame(p,bg=PANEL_BG); bf.pack(fill="x",padx=14,pady=8)
        tk.Button(bf,text="▶  START",command=self._start,bg="#0d3320",fg=OK_C,
                  font=("Consolas",9,"bold"),relief="flat",bd=0,padx=10,pady=6,
                  activebackground="#1a5535",cursor="hand2").pack(side="left",padx=(0,3))
        tk.Button(bf,text="■  STOP",command=self._stop,bg="#330d0d",fg=DANGER_C,
                  font=("Consolas",9,"bold"),relief="flat",bd=0,padx=10,pady=6,
                  cursor="hand2").pack(side="left",padx=3)
        tk.Button(bf,text="↺",command=self._reset,bg="#2a2210",fg=WARN_C,
                  font=("Consolas",10,"bold"),relief="flat",bd=0,padx=8,pady=6,
                  cursor="hand2").pack(side="left",padx=3)
        tk.Button(bf,text="📊",command=self._open_report,bg="#152230",fg=TEAL,
                  font=("Consolas",10),relief="flat",bd=0,padx=8,pady=6,
                  cursor="hand2").pack(side="left",padx=3)

        tk.Frame(p,bg=CARD_BORDER,height=1).pack(fill="x",padx=14,pady=4)
        self._sec(p,"RESOURCES")
        self.res_lbl={}
        for key,label,val,col in [("ambulances","Ambulances","2",ACCENT),
                                   ("team","Rescue Team","1",WARN_C),
                                   ("kits","Medical Kits","10",OK_C)]:
            rf=tk.Frame(p,bg=CARD_BG,pady=4); rf.pack(fill="x",padx=14,pady=2)
            tk.Label(rf,text=f"  {label}",bg=CARD_BG,fg=DIM,
                     font=("Consolas",8),anchor="w",width=14).pack(side="left",padx=4)
            lv=tk.Label(rf,text=val,bg=CARD_BG,fg=col,font=("Consolas",11,"bold"))
            lv.pack(side="right",padx=8); self.res_lbl[key]=lv

        tk.Frame(p,bg=CARD_BORDER,height=1).pack(fill="x",padx=14,pady=4)
        self._sec(p,"LEGEND")
        for col,label in [(FIRE_A,"Fire / Hazard"),(BLOCKED_C,"Blocked Road"),
                          (VICTIM_CRIT,"Critical Victim"),(VICTIM_MOD,"Moderate Victim"),
                          (VICTIM_MIN,"Minor Victim"),(BASE_C,"Rescue Base"),
                          (HOSP_C,"Medical Center"),(ROUTE_FAST,"Fast Route"),
                          (ROUTE_SAFE,"Safe Route"),(EXPLORE_C,"Explored Node"),
                          (FRONTIER_C,"Frontier Node")]:
            lf=tk.Frame(p,bg=PANEL_BG); lf.pack(fill="x",padx=18,pady=1)
            tk.Label(lf,text="●",fg=col,bg=PANEL_BG,font=("Consolas",10)).pack(side="left")
            tk.Label(lf,text=label,fg=DIM,bg=PANEL_BG,font=("Consolas",8)).pack(side="left",padx=4)

        tk.Frame(p,bg=CARD_BORDER,height=1).pack(fill="x",padx=14,pady=5)
        self._sec(p,"DECISION LOG")
        self.log_box=tk.Text(p,bg="#060a10",fg=TEXT,font=("Consolas",8),
                             wrap="word",state="disabled",bd=0,relief="flat")
        sb=tk.Scrollbar(p,command=self.log_box.yview,bg=PANEL_BG,
                        troughcolor=CARD_BG,width=8)
        self.log_box.config(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y",padx=(0,4),pady=(0,8))
        self.log_box.pack(fill="both",expand=True,padx=14,pady=(0,8))
        for tag,c in [("head",ACCENT),("info",TEXT),("ok",OK_C),
                      ("danger",DANGER_C),("warn",WARN_C),("route",TEAL),
                      ("ml",PURPLE),("fuzzy","#ffa657"),("csp",OK_C),
                      ("sa",WARN_C),("compare",DIM)]:
            self.log_box.tag_config(tag,foreground=c)

    def _build_map(self,parent):
        tk.Label(parent,text="CITY MAP — AIDRA v4",bg=BG,fg=ACCENT,
                 font=("Consolas",9,"bold")).pack(anchor="w",padx=12,pady=(6,2))
        mw=GRID_COLS*CELL+MAP_PAD_X*2; mh=GRID_ROWS*CELL+MAP_PAD_Y*2
        frame=tk.Frame(parent,bg="#030508",bd=2,relief="flat")
        frame.pack(padx=10,pady=4)
        self.canvas=tk.Canvas(frame,width=mw,height=mh,
                              bg="#030508",highlightthickness=0)
        self.canvas.pack()

    def _build_right(self,p):
        self._sec(p,"KPI DASHBOARD")
        self.kpi_lbl={}
        for key,lbl,init,col in [("saved","Victims Saved","0","ACCENT"),
                                   ("avg_time","Avg Rescue Time","–",TEXT),
                                   ("risk","Risk Exposure","–",DANGER_C),
                                   ("por","Path Optimality","–",WARN_C),
                                   ("util","Resource Util %","–",OK_C)]:
            kf=tk.Frame(p,bg=CARD_BG,pady=5); kf.pack(fill="x",padx=14,pady=2)
            tk.Label(kf,text=f"  {lbl}",bg=CARD_BG,fg=DIM,
                     font=("Consolas",8),anchor="w",width=18).pack(side="left",padx=4)
            fgc=ACCENT if col=="ACCENT" else col
            lv=tk.Label(kf,text=init,bg=CARD_BG,fg=fgc,font=("Consolas",10,"bold"))
            lv.pack(side="right",padx=8); self.kpi_lbl[key]=lv

        tk.Frame(p,bg=CARD_BORDER,height=1).pack(fill="x",padx=14,pady=4)
        self._sec(p,"FUZZY DECISION DETAIL")
        self.fuzzy_box=tk.Text(p,bg="#060a10",fg=TEXT,font=("Consolas",8),
                               height=10,bd=0,relief="flat",state="disabled")
        self.fuzzy_box.pack(fill="x",padx=14,pady=(0,4))

        tk.Frame(p,bg=CARD_BORDER,height=1).pack(fill="x",padx=14,pady=4)
        self._sec(p,"ALGO RUNTIME (ms)")
        self.rt_box=tk.Text(p,bg="#060a10",fg=TEXT,font=("Consolas",8),
                            height=6,bd=0,relief="flat",state="disabled")
        self.rt_box.pack(fill="x",padx=14,pady=(0,4))

        tk.Frame(p,bg=CARD_BORDER,height=1).pack(fill="x",padx=14,pady=4)
        self._sec(p,"ML METRICS")
        self.ml_box=tk.Text(p,bg="#060a10",fg=TEXT,font=("Consolas",8),
                            height=14,bd=0,relief="flat",state="disabled")
        self.ml_box.pack(fill="x",padx=14,pady=(0,4))
        self._fill_ml()

        tk.Frame(p,bg=CARD_BORDER,height=1).pack(fill="x",padx=14,pady=4)
        self._sec(p,"PERFORMANCE GRAPH")
        self.graph=tk.Canvas(p,bg="#060a10",height=130,highlightthickness=0,bd=0)
        self.graph.pack(fill="x",padx=14,pady=(0,10))

    def _fill_ml(self):
        _,_,_,km,nm,dm=train_models()
        self.ml_box.config(state="normal"); self.ml_box.delete("1.0","end")
        lines=[
            f"{'Model':<14}{'Acc':>6}{'Prec':>6}{'Rec':>6}{'F1':>6}",
            "─"*42,
            f"{'kNN (k=3)':<14}{km['acc']:6.3f}{km['prec']:6.3f}{km['rec']:6.3f}{km['f1']:6.3f}",
            f"{'Naive Bayes':<14}{nm['acc']:6.3f}{nm['prec']:6.3f}{nm['rec']:6.3f}{nm['f1']:6.3f}",
            f"{'Dec. Tree':<14}{dm['acc']:6.3f}{dm['prec']:6.3f}{dm['rec']:6.3f}{dm['f1']:6.3f}",
            "","CM kNN:",
            f"  TP={km['cm'][0][0]}  FP={km['cm'][0][1]}",
            f"  FN={km['cm'][1][0]}  TN={km['cm'][1][1]}",
            "CM Naive Bayes:",
            f"  TP={nm['cm'][0][0]}  FP={nm['cm'][0][1]}",
            f"  FN={nm['cm'][1][0]}  TN={nm['cm'][1][1]}",
            "CM Dec. Tree:",
            f"  TP={dm['cm'][0][0]}  FP={dm['cm'][0][1]}",
            f"  FN={dm['cm'][1][0]}  TN={dm['cm'][1][1]}",
        ]
        self.ml_box.insert("end","\n".join(lines))
        self.ml_box.config(state="disabled")

    def _draw_city(self,grid=None):
        c=self.canvas; c.delete("static")
        if grid is None: grid=GridMap()
        mw=GRID_COLS*CELL+MAP_PAD_X*2; mh=GRID_ROWS*CELL+MAP_PAD_Y*2
        c.create_rectangle(0,0,mw,mh,fill="#030508",outline="",tags="static")

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x1,y1=self._tl(row,col); x2,y2=x1+CELL,y1+CELL
                pos=(row,col)
                rr=(row%2==0); rc=(col%2==0)
                if pos in grid.blocked: fill="#100e18"
                elif rr or rc: fill=ROAD_MAIN
                else: fill=BLOCK_BG
                c.create_rectangle(x1,y1,x2,y2,fill=fill,outline="",tags="static")
                if pos not in grid.blocked:
                    if rr and not rc:
                        my=y1+CELL//2
                        c.create_line(x1,my,x2,my,fill="#2a3550",width=1,
                                      dash=(8,8),tags="static")
                        c.create_rectangle(x1,y1,x2,y1+5,fill=SIDEWALK_C,outline="",tags="static")
                        c.create_rectangle(x1,y2-5,x2,y2,fill=SIDEWALK_C,outline="",tags="static")
                    elif rc and not rr:
                        mx=x1+CELL//2
                        c.create_line(mx,y1,mx,y2,fill="#2a3550",width=1,
                                      dash=(8,8),tags="static")
                        c.create_rectangle(x1,y1,x1+5,y2,fill=SIDEWALK_C,outline="",tags="static")
                        c.create_rectangle(x2-5,y1,x2,y2,fill=SIDEWALK_C,outline="",tags="static")
                    elif rr and rc:
                        c.create_rectangle(x1,y1,x2,y2,fill="#192030",outline="",tags="static")
                    else:
                        c.create_rectangle(x1+4,y1+4,x2-4,y2-4,fill="#131825",
                                           outline="#0f1320",tags="static")
                        for wr in range(2):
                            for wc2 in range(3):
                                wx=x1+8+wc2*20; wy=y1+8+wr*26
                                if wx+12<x2-4 and wy+10<y2-4:
                                    c.create_rectangle(wx,wy,wx+10,wy+8,fill="#1a2540",
                                                       outline="#223050",tags="static")
                if pos in grid.blocked: self._draw_blocked(c,row,col)
                c.create_rectangle(x1,y1,x2,y2,fill="",outline="#0d1320",width=1,tags="static")

        for h in HOSPITALS: self._draw_hospital(c,h)
        self._draw_base(c,RESCUE_BASE)
        self._redraw_dynamic(grid)

    def _redraw_dynamic(self,grid=None):
        if grid is None: grid=self.agent.grid if self.agent else GridMap()
        c=self.canvas; c.delete("dynamic")
        victims=self.agent.victims if self.agent else list(VICTIMS_INIT)
        for v in victims:
            if v.get("status")=="rescued": continue
            self._draw_victim(c,v)
        for aid,pos in self.amb_pos.items():
            self._draw_ambulance(c,pos,aid)

    def _draw_blocked(self,c,row,col):
        x,y=self._cx(col),self._cy(row)
        c.create_oval(x-15,y-15,x+15,y+15,fill=BLOCKED_C,outline="#ff5555",
                      width=2,tags="static")
        c.create_rectangle(x-10,y-3,x+10,y+3,fill="white",outline="",tags="static")

    def _draw_hospital(self,c,pos):
        r,col=pos; x,y=self._cx(col),self._cy(r)
        c.create_oval(x-24,y-24,x+24,y+24,fill="#200008",outline=HOSP_C,
                      width=2,tags="static")
        c.create_rectangle(x-3,y-15,x+3,y+15,fill=HOSP_C,outline="",tags="static")
        c.create_rectangle(x-15,y-3,x+15,y+3,fill=HOSP_C,outline="",tags="static")
        c.create_text(x,y+30,text="MEDICAL\nCENTER",fill=HOSP_C,
                      font=("Consolas",6,"bold"),justify="center",tags="static")

    def _draw_base(self,c,pos):
        r,col=pos; x,y=self._cx(col),self._cy(r)
        c.create_rectangle(x-18,y-18,x+18,y+18,fill="#051025",outline=BASE_C,
                           width=2,tags="static")
        c.create_rectangle(x-3,y-12,x+3,y+12,fill=BASE_C,outline="",tags="static")
        c.create_rectangle(x-12,y-3,x+12,y+3,fill=BASE_C,outline="",tags="static")
        c.create_text(x,y+25,text="RESCUE\nBASE",fill=BASE_C,
                      font=("Consolas",6,"bold"),justify="center",tags="static")

    def _draw_victim(self,c,v):
        r,col=v["pos"]; x,y=self._cx(col),self._cy(r)
        sev=v["severity"]
        vc=VICTIM_CRIT if sev=="critical" else(VICTIM_MOD if sev=="moderate" else VICTIM_MIN)
        ph=self.tick*0.15
        pr=18+4*math.sin(ph+v["id"])
        c.create_oval(x-pr,y-pr,x+pr,y+pr,fill="",outline=vc,width=1,tags="dynamic")
        c.create_oval(x-12,y-12,x+12,y+12,fill="#0a0e18",outline=vc,width=2,tags="dynamic")
        c.create_oval(x-4,y-9,x+4,y-2,fill=vc,outline="",tags="dynamic")
        c.create_line(x,y-2,x,y+7,fill=vc,width=2,tags="dynamic")
        c.create_line(x-7,y+1,x+7,y+1,fill=vc,width=2,tags="dynamic")
        c.create_line(x,y+7,x-4,y+13,fill=vc,width=2,tags="dynamic")
        c.create_line(x,y+7,x+4,y+13,fill=vc,width=2,tags="dynamic")
        c.create_oval(x+7,y-16,x+17,y-6,fill=vc,outline="white",width=1,tags="dynamic")
        c.create_text(x+12,y-11,text=str(v["id"]),fill="white",
                      font=("Consolas",7,"bold"),tags="dynamic")

    def _draw_ambulance(self,c,pos,aid):
        r,col=pos; x,y=self._cx(col),self._cy(r); tag=f"amb{aid}"
        ox=-18 if aid==0 else 18; bx=x+ox; c.delete(tag)
        c.create_oval(bx-18,y+9,bx+18,y+15,fill="#000000",outline="",tags=tag)
        c.create_rectangle(bx-18,y-9,bx+18,y+9,fill="#e8ecf0",outline="#c0c8d0",
                           width=1,tags=tag)
        c.create_rectangle(bx-18,y-2,bx+18,y+1,fill=ACCENT,outline="",tags=tag)
        c.create_rectangle(bx-4,y-7,bx+4,y+5,fill=HOSP_C,outline="",tags=tag)
        c.create_rectangle(bx-8,y-3,bx+8,y+1,fill=HOSP_C,outline="",tags=tag)
        c.create_oval(bx-16,y+6,bx-8,y+14,fill="#222",outline="#444",tags=tag)
        c.create_oval(bx+8,y+6,bx+16,y+14,fill="#222",outline="#444",tags=tag)
        sc1=SIREN_R if (self.siren_phase+aid)%4<2 else "#440000"
        sc2=SIREN_B if (self.siren_phase+aid)%4>=2 else "#001144"
        c.create_oval(bx-12,y-14,bx-6,y-9,fill=sc1,outline="",tags=tag)
        c.create_oval(bx+6,y-14,bx+12,y-9,fill=sc2,outline="",tags=tag)
        c.create_text(bx,y-20,text=f"AMB-{aid+1}",fill=AMB_C,
                      font=("Consolas",6,"bold"),tags=tag)

    def _draw_expansion(self,node,kind,step):
        if node is None: return
        c=self.canvas; r,col=node
        x,y=self._cx(col),self._cy(r)
        if kind=="explore":
            it=c.create_rectangle(x-CELL//2+4,y-CELL//2+4,
                                   x+CELL//2-4,y+CELL//2-4,
                                   fill=EXPLORE_C,outline="",
                                   stipple="gray25",tags="expand")
        else:
            it=c.create_rectangle(x-CELL//2+6,y-CELL//2+6,
                                   x+CELL//2-6,y+CELL//2-6,
                                   fill=FRONTIER_C,outline="",
                                   stipple="gray25",tags="expand")
        self.expand_items.append(it)
        if len(self.expand_items)>120:
            old=self.expand_items.pop(0)
            try: c.delete(old)
            except: pass

    def _draw_final_path(self,path):
        c=self.canvas
        if not path: return
        for pos in path:
            r,col=pos; x,y=self._cx(col),self._cy(r)
            it=c.create_oval(x-5,y-5,x+5,y+5,fill=PATH_FINAL,outline="",tags="expand")
            self.expand_items.append(it)

    def _expand_cb(self,node,kind,data):
        def _do():
            if kind=="path":
                self._draw_final_path(data)
            else:
                self._draw_expansion(node,kind,data)
        self.root.after(0,_do)

    def _draw_fire_layer(self,grid):
        c=self.canvas; c.delete("fire"); ph=self.fire_phase
        for (r,col) in grid.fire:
            x,y=self._cx(col),self._cy(r)
            c.create_oval(x-22,y-22,x+22,y+22,fill="#1a0600",outline="",tags="fire")
            wo=math.sin(ph*0.25+r*1.3+col*0.9)*4
            wi=math.sin(ph*0.4+r+col)*3
            pts_o=[x,y-22+wo,x+10,y-6,x+16,y+10,x,y+5,x-16,y+10,x-10,y-6]
            c.create_polygon(pts_o,fill=FIRE_B,outline="",smooth=True,tags="fire")
            pts_m=[x,y-14+wi,x+7,y-2,x+10,y+8,x,y+3,x-10,y+8,x-7,y-2]
            c.create_polygon(pts_m,fill=FIRE_A,outline="",smooth=True,tags="fire")
            pts_i=[x,y-7+int(wi/2),x+4,y+2,x+6,y+8,x,y+4,x-6,y+8,x-4,y+2]
            c.create_polygon(pts_i,fill=FIRE_C,outline="",smooth=True,tags="fire")
            c.create_oval(x-3,y,x+3,y+8,fill=FIRE_D,outline="",tags="fire")
            if ph%3==0:
                for _ in range(2):
                    sx=x+random.randint(-10,10); sy=y+random.randint(-15,-5)
                    c.create_oval(sx-2,sy-2,sx+2,sy+2,fill=FIRE_D,outline="",tags="fire")

    def _draw_route(self,path,risk):
        c=self.canvas
        for it in self.route_items:
            try: c.delete(it)
            except: pass
        self.route_items=[]
        if not path or len(path)<2: return
        color=ROUTE_SAFE if risk>0.2 else ROUTE_FAST
        offset=self.tick%12
        for i in range(len(path)-1):
            r1,c1=path[i]; r2,c2=path[i+1]
            x1,y1=self._cx(c1),self._cy(r1); x2,y2=self._cx(c2),self._cy(r2)
            it=c.create_line(x1,y1,x2,y2,fill=color,width=3,
                             arrow="last" if i==len(path)-2 else "none",
                             arrowshape=(10,12,4),dash=(10,6),
                             dashoffset=offset,tags="route")
            self.route_items.append(it)

    def _animate(self):
        self.tick+=1; self.fire_phase+=1
        if self.tick%2==0: self.siren_phase+=1
        self.clock_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        grid=self.agent.grid if self.agent else GridMap()
        self._draw_fire_layer(grid)
        self._redraw_dynamic(grid)
        for aid,pos in self.amb_pos.items():
            self._draw_ambulance(self.canvas,pos,aid)
        self.root.after(80,self._animate)

    def _map_cb(self,event,data,aid,extra):
        def _do():
            if event=="move": self.amb_pos[aid]=data
            elif event=="route": self._draw_route(data,extra)
            elif event in("rescued","update"):
                grid=self.agent.grid if self.agent else None
                self._draw_city(grid)
                self.canvas.delete("expand"); self.expand_items.clear()
        self.root.after(0,_do)

    def _log_cb(self,msg,style):
        def _do():
            self.log_box.config(state="normal")
            self.log_box.insert("end",msg+"\n",style)
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.root.after(0,_do)

    def _fuzzy_cb(self,d):
        def _do():
            self.fuzzy_box.config(state="normal")
            self.fuzzy_box.delete("1.0","end")
            lines=[
                f"Hazard    : {d['hazard']:.3f}",
                f"Dist ratio: {d['dist_ratio']:.3f}",
                f"Urgency   : {d['urgency']}",
                "─"*28,
                f"haz_low={d['hazard_low']:.2f}  haz_med={d['hazard_med']:.2f}",
                f"haz_hi ={d['hazard_hi']:.2f}",
                f"urg_lo ={d['urgency_lo']:.2f}  urg_hi={d['urgency_hi']:.2f}",
                f"d_ok   ={d['dist_ok']:.2f}   d_lng={d['dist_long']:.2f}",
                "─"*28,
                f"SAFE={d['safe_weight']:.3f}  FAST={d['fast_weight']:.3f}",
                f"Score: {d['score']:.3f}",
                f"→ {d['reason']}",
            ]
            self.fuzzy_box.insert("end","\n".join(lines))
            self.fuzzy_box.config(state="disabled")
        self.root.after(0,_do)

    def _kpi_cb(self,kpis):
        def _do():
            total=kpis.get("total",5)
            self.kpi_lbl["saved"].config(text=f"{kpis['saved']} / {total}")
            self.kpi_lbl["avg_time"].config(text=f"{kpis['avg_time']}s")
            self.kpi_lbl["risk"].config(text=f"{kpis['risk']:.3f}")
            self.kpi_lbl["por"].config(text=f"{kpis['por']:.3f}")
            self.kpi_lbl["util"].config(text=f"{kpis['util']}%")
            if self.agent: self.res_lbl["kits"].config(text=str(kpis["kits"]))
            rt=kpis.get("runtimes",{})
            if rt:
                self.rt_box.config(state="normal"); self.rt_box.delete("1.0","end")
                lines=[f"  {name:<8}: {ms:.2f} ms" for name,ms in rt.items()]
                self.rt_box.insert("end","\n".join(lines))
                self.rt_box.config(state="disabled")
            self._draw_graph()
        self.root.after(0,_do)

    def _draw_graph(self):
        g=self.graph; g.delete("all")
        W=g.winfo_width() or 290; H=130
        if not self.agent: return
        times=self.agent.kpis["times"]; risks=self.agent.kpis["risks"]
        if not times: return
        mt=max(times) if times else 1; n=len(times)
        bw=max(8,(W-50)//(n*2+1))
        g.create_text(12,10,text="■ Time",fill=ACCENT,font=("Consolas",7),anchor="w")
        g.create_text(60,10,text="■ Risk",fill=DANGER_C,font=("Consolas",7),anchor="w")
        for i,(t,r) in enumerate(zip(times,risks)):
            x=22+i*(bw*2+6); th=int((t/mt)*(H-28)); rh=int(r*(H-28))
            g.create_rectangle(x,H-12-th,x+bw,H-12,fill=ACCENT,outline="")
            g.create_rectangle(x+bw+2,H-12-rh,x+bw*2+2,H-12,fill=DANGER_C,outline="")
            g.create_text(x+bw,H-4,text=str(i+1),fill=DIM,font=("Consolas",6))
        g.create_line(20,H-12,W-10,H-12,fill=CARD_BORDER,width=1)
        g.create_line(20,10,20,H-12,fill=CARD_BORDER,width=1)

    def _on_speed(self,val):
        if self.agent: self.agent.delay=float(val)

    def _start(self):
        if self.agent and self.agent.running: return
        self._reset_state()
        self.agent=Agent(log_cb=self._log_cb,kpi_cb=self._kpi_cb,
                         map_cb=self._map_cb,fuzzy_cb=self._fuzzy_cb,
                         expand_cb=self._expand_cb)
        self.agent.algo=self.algo_var.get()
        self.agent.delay=self.speed_var.get()
        self.agent.show_expansion=self.show_exp_var.get()
        self._draw_city(self.agent.grid)
        threading.Thread(target=self.agent.run,daemon=True).start()

    def _stop(self):
        if self.agent: self.agent.running=False
        self._log_cb("[SIMULATION STOPPED]","danger")

    def _reset(self):
        if self.agent: self.agent.running=False
        self._reset_state(); self._draw_city()

    def _reset_state(self):
        self.agent=None
        self.amb_pos={0:RESCUE_BASE,1:RESCUE_BASE}
        self.route_items=[]; self.expand_items=[]
        self.canvas.delete("expand"); self.canvas.delete("route")
        self.log_box.config(state="normal")
        self.log_box.delete("1.0","end"); self.log_box.config(state="disabled")
        for k,v in [("saved","0"),("avg_time","–"),("risk","–"),
                    ("por","–"),("util","–")]:
            self.kpi_lbl[k].config(text=v)
        for k,v in [("ambulances","2"),("team","1"),("kits","10")]:
            self.res_lbl[k].config(text=v)
        self.graph.delete("all")
        self.fuzzy_box.config(state="normal"); self.fuzzy_box.delete("1.0","end")
        self.fuzzy_box.config(state="disabled")
        self.rt_box.config(state="normal"); self.rt_box.delete("1.0","end")
        self.rt_box.config(state="disabled")
        self._log_cb("System ready.  Press ▶ START to deploy.","info")

    def _open_report(self):
        rpt=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "aidra_performance_report.csv")
        if not os.path.exists(rpt):
            messagebox.showinfo("Report","No report yet. Run a simulation first."); return
        win=tk.Toplevel(self.root); win.title("Performance Report")
        win.configure(bg=PANEL_BG); win.geometry("760x340")
        t=tk.Text(win,bg="#060a10",fg=TEXT,font=("Consolas",9),bd=0,relief="flat")
        t.pack(fill="both",expand=True,padx=10,pady=10)
        with open(rpt) as f: t.insert("end",f.read())
        t.config(state="disabled")

# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════
def main():
    if not os.path.exists(CSV_PATH): generate_csv_dataset(CSV_PATH)
    root=tk.Tk()
    style=ttk.Style(); style.theme_use("clam")
    style.configure("TCombobox",fieldbackground=CARD_BG,background=CARD_BG,
                    foreground=TEXT,selectbackground=ACCENT,insertcolor=TEXT)
    style.map("TCombobox",fieldbackground=[("readonly",CARD_BG)],
              foreground=[("readonly",TEXT)])
    app=AIDRA_GUI(root)
    root.mainloop()

if __name__=="__main__":
    main()

