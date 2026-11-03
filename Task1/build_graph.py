import csv, json
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

def clean(s): return " ".join((s or "").strip().split())

def build():
    with (BASE / "works.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    nodes, edges, rejected = {}, {}, []
    def node(key, typ, props):
        if key in nodes and nodes[key]["type"] != typ: raise ValueError(f"ID collision: {key}")
        nodes.setdefault(key, {"id":key, "type":typ, "properties":{}})
        for k,v in props.items():
            if v and k in nodes[key]["properties"] and nodes[key]["properties"][k] != v:
                raise ValueError(f"Conflicting {k} for {key}")
            if v: nodes[key]["properties"][k] = v
    def edge(src, rel, dst, evidence):
        if src not in nodes or dst not in nodes: raise ValueError("Relationship endpoint missing")
        key=f"{src}|{rel}|{dst}"
        edges.setdefault(key,{"id":key,"source":src,"type":rel,"target":dst,"provenance":evidence})
    for line,r in enumerate(rows,2):
        doi=clean(r.get("DOI")).lower(); title=clean(r.get("title")); year=clean(r.get("year")); oa_id=clean(r.get("openalex_id"))
        if (not doi and not oa_id) or not title or not year.isdigit():
            rejected.append({"line":line,"reason":"OpenAlex ID or DOI, title, or valid year missing"}); continue
        w=f"work:{oa_id or 'doi:'+doi}"; url=clean(r.get("source_url"))
        node(w,"Work",{"openalex_id":oa_id,"doi":doi,"title":title,"year":year,"source_url":url,"work_type":clean(r.get("work_type"))})
        names=[clean(x) for x in r.get("authors","").split("|")]
        author_ids=[clean(x) for x in r.get("author_ids","").split("|")]
        for i,name in enumerate(names):
            if not name: continue
            ident=author_ids[i] if i<len(author_ids) and author_ids[i] else 'name:'+name.casefold()
            a=f"person:{ident}"; node(a,"Person",{"openalex_id":author_ids[i] if i<len(author_ids) else "","name":name}); edge(w,"AUTHORED_BY",a,url)
        venue=clean(r.get("venue"))
        if venue:
            venue_id=clean(r.get("venue_id")); v=f"venue:{venue_id or 'name:'+venue.casefold()}"; node(v,"Venue",{"openalex_id":venue_id,"name":venue}); edge(w,"PUBLISHED_IN",v,url)
    allowed={("Work","AUTHORED_BY","Person"),("Work","PUBLISHED_IN","Venue")}
    for e in edges.values():
        assert (nodes[e["source"]]["type"],e["type"],nodes[e["target"]]["type"]) in allowed
    graph={"schema_version":"1.0","nodes":list(nodes.values()),"edges":list(edges.values()),"rejected_rows":rejected}
    (OUT/"graph.json").write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding="utf-8")
    # Flat, label-specific CSVs for Neo4j Desktop's local LOAD CSV import.
    ni=BASE/"neo4j_import"; ni.mkdir(exist_ok=True)
    for typ,filename,columns in [("Work","works.csv",["title","doi","year","source_url"]),("Person","people.csv",["name"]),("Venue","venues.csv",["name"])]:
        with (ni/filename).open("w",encoding="utf-8",newline="") as f:
            wr=csv.writer(f); wr.writerow(["id",*columns])
            for n in nodes.values():
                if n["type"]==typ: wr.writerow([n["id"],*[n["properties"].get(c,"") for c in columns]])
    for rel,filename in [("AUTHORED_BY","authored_by.csv"),("PUBLISHED_IN","published_in.csv")]:
        with (ni/filename).open("w",encoding="utf-8",newline="") as f:
            wr=csv.writer(f); wr.writerow(["start_id","end_id","provenance"])
            for e in edges.values():
                if e["type"]==rel: wr.writerow([e["source"],e["target"],e["provenance"]])
    return {"works":sum(n["type"]=="Work" for n in nodes.values()),
            "people":sum(n["type"]=="Person" for n in nodes.values()),
            "venues":sum(n["type"]=="Venue" for n in nodes.values()),
            "relationships":len(edges),"rejected_rows":len(rejected)}

print(json.dumps(build(),indent=2))
