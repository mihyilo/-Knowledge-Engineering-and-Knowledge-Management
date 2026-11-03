"""
python fetch_openalex.py --query "graph data integration" --from-year 2018 --to-year 2025 --limit 100
"""
import argparse, csv, json, os, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE=Path(__file__).resolve().parent
API="https://api.openalex.org/works"

def unpack_abstract(index):
    if not index: return ""
    words=[]
    for word,positions in index.items():
        for pos in positions: words.append((pos,word))
    return " ".join(w for _,w in sorted(words))

def fetch(query, start_year, end_year, limit, email=None):
    key=os.getenv("OPENALEX_API_KEY","").strip()
    select="id,doi,title,publication_year,authorships,primary_location,abstract_inverted_index,type"
    cursor="*"; results=[]
    while len(results)<limit:
        params={"search":query,"filter":f"from_publication_date:{start_year}-01-01,to_publication_date:{end_year}-12-31","per_page":min(100,limit-len(results)),"cursor":cursor,"select":select}
        if key: params["api_key"]=key
        if email: params["mailto"]=email
        req=Request(API+"?"+urlencode(params),headers={"User-Agent":"Task1KnowledgeGraph/1.0 (mailto:"+(email or "")+")","Accept":"application/json"})
        try:
            with urlopen(req,timeout=30) as response: page=json.load(response)
        except HTTPError as e:
            detail=e.read().decode("utf-8","replace")[:1000]
            raise RuntimeError(f"OpenAlex returned HTTP {e.code}: {detail}") from e
        except URLError as e:
            raise RuntimeError(f"Could not reach OpenAlex ({e}). Check internet/DNS/proxy settings.") from e
        works=page.get("results",[])
        if not works: break
        results.extend(works)
        cursor=(page.get("meta") or {}).get("next_cursor")
        if not cursor: break
        time.sleep(.12)
    return results[:limit]

p=argparse.ArgumentParser(description="Search OpenAlex and save works.csv plus abstracts.csv")
p.add_argument("--query",default="graph data integration",help="OpenAlex search phrase")
p.add_argument("--from-year",type=int,default=2018)
p.add_argument("--to-year",type=int,default=2025)
p.add_argument("--limit",type=int,default=100)
p.add_argument("--email",help="Optional contact email for API etiquette")
a=p.parse_args()
if a.from_year>a.to_year or a.limit<1: p.error("invalid year range or limit")
works=fetch(a.query,a.from_year,a.to_year,a.limit,a.email)
fields=["openalex_id","DOI","title","year","venue","authors","author_ids","venue_id","source_url","work_type"]
with (BASE/"works.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for x in works:
        authorships=x.get("authorships") or []
        # Keep names and IDs positionally aligned; OpenAlex can return nulls.
        authors=[str((z.get("author") or {}).get("display_name") or "") for z in authorships]
        author_ids=[str((z.get("author") or {}).get("id") or "") for z in authorships]
        source=((x.get("primary_location") or {}).get("source") or {})
        w.writerow({"openalex_id":x.get("id",""),"DOI":x.get("doi") or "","title":x.get("title") or "","year":x.get("publication_year") or "","venue":source.get("display_name","") or "","authors":"|".join(authors),"author_ids":"|".join(author_ids),"venue_id":source.get("id","") or "","source_url":x.get("doi") or x.get("id",""),"work_type":x.get("type","")})
with (BASE/"abstracts.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["openalex_id","doi","title","abstract","source_url"]); w.writeheader()
    for x in works:
        abstract=unpack_abstract(x.get("abstract_inverted_index"))
        w.writerow({"openalex_id":x.get("id",""),"doi":x.get("doi") or "","title":x.get("title") or "","abstract":abstract,"source_url":x.get("doi") or x.get("id","")})
(BASE/"openalex_query.json").write_text(json.dumps({"query":a.query,"from_year":a.from_year,"to_year":a.to_year,"limit":a.limit,"retrieved_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"returned":len(works),"abstracts_returned":sum(bool(x.get("abstract_inverted_index")) for x in works)},ensure_ascii=False,indent=2),encoding="utf-8")
print(f"Saved {len(works)} works; {sum(bool(x.get('abstract_inverted_index')) for x in works)} have abstracts.")

