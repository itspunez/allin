import base64,hashlib,json,os,re,time
from pathlib import Path
from urllib.parse import urlparse
import requests,yaml

API="https://api.github.com"; STATE=Path("state/discovered_sources.json")
UA="proxy-aggregator-discovery/2.0"
URL_RE=re.compile(r"https?://[^\s<>\"]+",re.I)
KEYWORDS=("vless","vmess","trojan","ss://","shadowsocks","subscription","sub","clash","sing-box","mihomo","proxy_configs","proxies.txt","base64")

def cfg():
    with open("discovery.yml",encoding="utf-8") as f:return yaml.safe_load(f) or {}
def headers():
    h={"Accept":"application/vnd.github+json","User-Agent":UA,"X-GitHub-Api-Version":"2026-03-10"}
    if os.getenv("GITHUB_TOKEN"):h["Authorization"]=f"Bearer {os.getenv('GITHUB_TOKEN')}"
    return h
def get(url,params=None):
    for n in range(4):
        r=requests.get(url,headers=headers(),params=params,timeout=20)
        if r.status_code in (403,429):
            wait=2**n
            if r.headers.get("X-RateLimit-Remaining")=="0":
                wait=max(1,min(120,int(r.headers.get("X-RateLimit-Reset","0"))-int(time.time())))
            time.sleep(wait);continue
        r.raise_for_status();return r
    raise RuntimeError("GitHub API retry/rate limit exhausted")
def clean(url):
    p=urlparse(url.rstrip(".,);]}>'\""))
    if p.scheme not in ("http","https") or not p.netloc:return None
    return p._replace(fragment="").geturl()
def valid(url):
    p=urlparse(url);allowed=set(cfg()["github"].get("allowed_hosts",[]))
    return p.netloc.lower() in allowed and any(k in url.lower() for k in KEYWORDS)
def sid(url):return "gh-"+hashlib.sha1(url.encode()).hexdigest()[:16]
def readme(full):
    owner,name=full.split("/",1)
    r=get(f"{API}/repos/{owner}/{name}/readme")
    try:return base64.b64decode(r.json().get("content","")).decode("utf-8","replace")
    except Exception:return ""
def run():
    c=cfg()["github"]
    if not c.get("enabled",True):return
    repos={}
    for q in c.get("queries",[]):
        try:
            data=get(f"{API}/search/repositories",{"q":q,"sort":"updated","order":"desc","per_page":int(c.get("max_repositories_per_query",20))}).json()
            for x in data.get("items",[]):repos[x["full_name"]]=x
        except Exception as e:print("[DISCOVERY]",q,e)
    found={}
    for repo in list(repos.values())[:int(c.get("max_total_candidates",100))]:
        try:text=readme(repo["full_name"])
        except Exception:continue
        for raw in URL_RE.findall(text):
            u=clean(raw)
            if not u or not valid(u):continue
            found[sid(u)]={"id":sid(u),"name":"GitHub: "+repo["full_name"],"url":u,
              "enabled":True,"weight":min(100,50+min(30,int(repo.get("stargazers_count",0)))+min(20,int(repo.get("forks_count",0)))),
              "format":"auto","tags":["discovered","github"],"repo":repo["full_name"],
              "stars":int(repo.get("stargazers_count",0)),"forks":int(repo.get("forks_count",0)),
              "repo_updated_at":repo.get("updated_at","")}
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(found,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"[DISCOVERY] {len(found)} sources")
if __name__=="__main__":run()
