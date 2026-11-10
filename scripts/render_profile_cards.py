
#!/usr/bin/env python3
# Animated SVG profile-card renderer. STATIC=1 emits still final-frame cards.
import base64, datetime as dt, html, json, os, re, subprocess, sys, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
USER="SOUMYADEEPDEY1217"; NAME="Soumyadeep Dey"
CYAN="#00C2FF"; BG="#07111F"; PANEL="#0B1B2B"; WHITE="#EAF6FF"; MUTED="#8FAABD"
FONT="'Fira Code','JetBrains Mono',monospace"
PROFILE=f"https://github.com/{USER}"
LINKEDIN="https://www.linkedin.com/in/soumyadeepdey-"
PORTFOLIO="https://soumyadeepdey1217.github.io/portfolio/"
DATA=Path(os.getenv("CONTRIBUTIONS_JSON",ROOT/"data/contributions.json"))
OUT=Path(os.getenv("OUTPUT_DIR",ROOT/"cards"))
STATIC=os.getenv("STATIC","").lower() in ("1","true","yes")
REPOS=[
("TrailMind AI","TrailMind-AI","An AI companion that nudges people outdoors and helps them touch grass.","React · Vite · FastAPI · PostgreSQL · AI","https://github.com/SOUMYADEEPDEY1217/TrailMind-AI"),
("PitchCraft AI","PitchCraft-AI","An AI-powered workspace for shaping stronger startup pitches.","React · FastAPI · LLMs · Database","https://github.com/SOUMYADEEPDEY1217/PitchCraft-AI"),
("Stationery Store Management","stationery-store-management-system","A practical store-management system for campus workflows.","HTML · CSS · JavaScript · Backend","https://github.com/SOUMYADEEPDEY1217/stationary-store-management-system"),
("GhostNote AI","GHOSTNOTE","A Hacktoberfest build exploring the ghost-in-the-machine idea.","AI · Web · Open Source","https://github.com/SOUMYADEEPDEY1217/GHOSTNOTE")]

def esc(v): return html.escape(str(v),quote=True)
def tx(x,y,s,size=14,color=WHITE,weight=400,anchor="start"):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>'

def svg(w,h,body,delay=0,font64=""):
    motion=""
    if not STATIC:
        motion=(f'<style>@keyframes enter{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}'
        f'@keyframes halo{{0%,100%{{filter:drop-shadow(0 0 2px {CYAN}55)}}50%{{filter:drop-shadow(0 0 10px {CYAN}AA)}}}}'
        f'.card{{opacity:0;animation:enter .8s cubic-bezier(.2,.8,.2,1) {delay}s both}}'
        f'.halo{{animation:halo 3.2s ease-in-out infinite}}'
        f'@media(prefers-reduced-motion:reduce){{*,*::before,*::after{{animation:none!important;transition:none!important}}.card{{opacity:1;transform:none}}}}</style>')
    fontcss=(f'<style>@font-face{{font-family:"Fira Code";src:url(data:font/woff2;base64,{font64}) format("woff2");font-weight:400 700}}</style>' if font64 else "")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<title>{NAME} GitHub profile card</title>{fontcss}{motion}
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="{BG}"/><stop offset="1" stop-color="#102B42"/></linearGradient>
<linearGradient id="cyan"><stop stop-color="{CYAN}"/><stop offset="1" stop-color="#8BE9FF"/></linearGradient>
<pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="{CYAN}" stroke-opacity=".08"/></pattern></defs>
<rect width="100%" height="100%" rx="22" fill="url(#bg)"/><rect width="100%" height="100%" rx="22" fill="url(#grid)"/>
<rect x="18" y="18" width="{w-36}" height="{h-36}" rx="16" fill="{PANEL}" fill-opacity=".82" stroke="{CYAN}" stroke-opacity=".25"/>{body}</svg>'''

def fetch():
    token=os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        if DATA.exists(): return json.loads(DATA.read_text())
        raise RuntimeError("No contribution JSON. Run with GITHUB_TOKEN to fetch it.")
    query=("query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{"
           "totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}")
    payload=json.dumps({"query":query,"variables":{"login":USER}}).encode()
    req=urllib.request.Request("https://api.github.com/graphql",data=payload,
      headers={"Authorization":f"Bearer {token}","Content-Type":"application/json","User-Agent":"profile-svg-cards"})
    result=json.load(urllib.request.urlopen(req,timeout=30))
    if result.get("errors") or not result.get("data",{}).get("user"):
        raise RuntimeError("GitHub GraphQL error: "+json.dumps(result.get("errors","User not found")))
    cal=result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    data={"username":USER,"updated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
          "total_contributions":cal["totalContributions"],
          "days":[d for week in cal["weeks"] for d in week["contributionDays"]]}
    DATA.parent.mkdir(parents=True,exist_ok=True); DATA.write_text(json.dumps(data,indent=2))
    return data

def stats(data):
    days=sorted(data["days"],key=lambda d:d["date"]); months=defaultdict(int); weekdays=Counter(); active=set()
    for d in days:
        date=dt.date.fromisoformat(d["date"]); n=int(d["contributionCount"]); months[date.strftime("%b")]+=n
        if n: active.add(date); weekdays[date.strftime("%A")]+=n
    cur=dt.date.today() if dt.date.today() in active else dt.date.today()-dt.timedelta(days=1)
    streak=0
    while cur in active: streak+=1; cur-=dt.timedelta(days=1)
    longest=run=0
    for d in days:
        run=run+1 if int(d["contributionCount"]) else 0; longest=max(longest,run)
    return {"days":days,"months":months,"active":len(active),"streak":streak,"longest":longest,
            "busy":weekdays.most_common(1)[0][0] if weekdays else "—",
            "total":int(data.get("total_contributions",0))}

def font_subset():
    d=OUT/"_font"; d.mkdir(parents=True,exist_ok=True); src=d/"FiraCode-Regular.ttf"; dst=d/"FiraCode-subset.woff2"
    if not src.exists():
        try:
            req=urllib.request.Request("https://github.com/tonsky/FiraCode/raw/master/distr/ttf/FiraCode-Regular.ttf",headers={"User-Agent":"profile-svg-cards"})
            src.write_bytes(urllib.request.urlopen(req,timeout=20).read())
        except Exception: return ""
    try:
        subprocess.run([sys.executable,"-m","fontTools.subset",str(src),f"--output-file={dst}","--flavor=woff2","--unicodes=U+0000-00FF,U+2000-206F"],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return base64.b64encode(dst.read_bytes()).decode()
    except Exception: return ""

def render_hero(f):
    b='<g class="card"><rect x="42" y="42" width="7" height="174" rx="3" fill="url(#cyan)"/>'
    b+=tx(76,105,NAME,38,WHITE,700)+tx(78,145,"Building intelligent products with thoughtful engineering.",16,CYAN,500)
    b+=tx(78,180,"AI / ML  ·  Full Stack  ·  Game Development  ·  Cybersecurity",12,MUTED)
    b+=f'<a xlink:href="{PROFILE}"><rect x="78" y="197" width="142" height="30" rx="15" fill="{CYAN}" fill-opacity=".14" stroke="{CYAN}"/>{tx(149,217,"GITHUB PROFILE",10,CYAN,600,"middle")}</a>'
    portrait=os.getenv("PORTRAIT_URL","")
    if portrait.startswith("https://"):
        b+=f'<clipPath id="pc"><circle cx="866" cy="130" r="75"/></clipPath><image xlink:href="{esc(portrait)}" x="791" y="55" width="150" height="150" preserveAspectRatio="xMidYMid slice" clip-path="url(#pc)"/><circle cx="866" cy="130" r="77" fill="none" stroke="{CYAN}" stroke-width="2"/>'
    else: b+=f'<circle cx="866" cy="130" r="75" fill="#10263A" stroke="{CYAN}"/>{tx(866,125,"SD",38,CYAN,700,"middle")}{tx(866,150,"ENGINEER",9,MUTED,500,"middle")}'
    OUT.joinpath("hero.svg").write_text(svg(1000,260,b+"</g>",0,f))

def render_links(f):
    tiles=[("github","GITHUB","Code · Open source",PROFILE,"⌘"),
           ("linkedin","LINKEDIN","Connect · Collaborate",LINKEDIN,"in"),
           ("portfolio","PORTFOLIO","Selected work · Projects",PORTFOLIO,"↗")]
    for i,(slug,title,sub,url,symbol) in enumerate(tiles):
        body=f'<a xlink:href="{url}"><g class="card"><rect x="12" y="12" width="300" height="94" rx="14" fill="#10263A" stroke="{CYAN}" stroke-opacity=".45"/><circle cx="52" cy="59" r="22" fill="{CYAN}" fill-opacity=".13" stroke="{CYAN}"/>'
        body+=tx(52,65,symbol,17,CYAN,700,"middle")+tx(88,52,title,15,WHITE,700)+tx(88,76,sub,10,MUTED)+"</g></a>"
        OUT.joinpath(f"link-{slug}.svg").write_text(svg(324,118,body,.2+i*.15,f))

def render_activity(m,f):
    b='<g class="card">'+tx(42,60,"CONTRIBUTION PULSE",18,WHITE,700)+tx(42,84,"A month-by-month view of consistent building.",11,MUTED)
    for i,(label,val) in enumerate([("CURRENT STREAK",f'{m["streak"]} days'),("LONGEST STREAK",f'{m["longest"]} days'),("ACTIVE DAYS",str(m["active"])),("BUSIEST DAY",m["busy"])]):
        x=42+i*230; b+=f'<rect x="{x}" y="104" width="210" height="66" rx="10" fill="#10263A" stroke="{CYAN}" stroke-opacity=".2"/>'
        b+=tx(x+14,130,label,9,MUTED,600)+tx(x+14,154,val,18,CYAN,700)
    months=[]
    for d in m["days"]:
        mo=dt.date.fromisoformat(d["date"]).strftime("%b")
        if mo not in months: months.append(mo)
    months=months[-12:]; vals=[m["months"].get(x,0) for x in months]; mx=max(vals or [1])
    for i,(mo,v) in enumerate(zip(months,vals)):
        x=54+i*73; h=max(3,int(78*v/mx))
        b+=f'<rect x="{x}" y="{285-h}" width="48" height="{h}" rx="5" fill="url(#cyan)"/>'
        b+=tx(x+24,304,mo.upper(),8,MUTED,500,"middle")+tx(x+24,277-h,str(v),8,WHITE,500,"middle")
    b+=tx(954,60,f'{m["total"]:,} total',11,CYAN,600,"end")+"</g>"
    OUT.joinpath("activity.svg").write_text(svg(1000,330,b,.65,f))

def render_repo(repo,i,f):
    name,slug,desc,stack,url=repo; b='<g class="card"><rect x="42" y="42" width="5" height="106" rx="2" fill="'+CYAN+'"/>'
    b+=tx(68,73,name,22,WHITE,700)+tx(68,105,desc,12,MUTED)+tx(68,132,stack,10,CYAN,500)
    b+=f'<a xlink:href="{url}"><rect x="806" y="76" width="142" height="38" rx="19" fill="{CYAN}" fill-opacity=".13" stroke="{CYAN}"/>{tx(877,100,"VIEW REPOSITORY  ↗",9,CYAN,700,"middle")}</a></g>'
    filename=re.sub(r"[^a-z0-9]+","-",slug.lower()).strip("-")
    OUT.joinpath(f"repo-{filename}.svg").write_text(svg(1000,190,b,1+i*.18,f))

def render_graph(m,f):
    colors=["#142638","#07506A","#08799B","#00A6D6",CYAN]; days=m["days"][-371:]
    if days: days=[None]*((dt.date.fromisoformat(days[0]["date"]).weekday()+1)%7)+days
    mx=max([int(d["contributionCount"]) for d in days if d] or [1])
    b='<g class="card">'+tx(42,56,"CONTRIBUTION MAP",16,WHITE,700)+tx(954,56,f'{m["total"]:,} contributions',10,CYAN,600,"end")
    for i,d in enumerate(days):
        if d is None: continue
        n=int(d["contributionCount"]); level=0 if n==0 else min(4,max(1,int(n/mx*4)+1))
        x=42+(i//7)*13; y=76+(i%7)*13
        if x+10<=955: b+=f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{colors[level]}"/>'
    b+=tx(42,166,"Less",8,MUTED)
    for i,c in enumerate(colors): b+=f'<rect x="{80+i*16}" y="157" width="10" height="10" rx="2" fill="{c}"/>'
    b+=tx(184,166,"More",8,MUTED)+"</g>"
    OUT.joinpath("contributions.svg").write_text(svg(1000,190,b,1.9,f))

def main():
    OUT.mkdir(parents=True,exist_ok=True); m=stats(fetch()); f=font_subset()
    render_hero(f); render_links(f); render_activity(m,f)
    for i,r in enumerate(REPOS): render_repo(r,i,f)
    render_graph(m,f)
    print(f"Rendered {OUT}; contributions={m['total']}; STATIC={int(STATIC)}")
if __name__=="__main__": main()
