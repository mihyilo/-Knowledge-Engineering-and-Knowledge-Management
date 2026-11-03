import json
from html import escape
from pathlib import Path

from pyvis.network import Network

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "output" / "graph.json"
TARGET = BASE / "output" / "knowledge_graph_interactive.html"
COLORS = {"Work":"#42b7c8", "Person":"#e8aa50", "Venue":"#a286db", "Topic":"#6abd78", "Method":"#e77e8b", "Technology":"#6099e2", "DataProblem":"#e58a50"}

data=json.loads(SOURCE.read_text(encoding="utf-8"))
net=Network(height="850px",width="100%",directed=True,bgcolor="#101923",font_color="#eef4fa",cdn_resources="in_line",notebook=False)
net.set_options("""
{"nodes":{"shape":"dot","font":{"size":15,"face":"Arial","color":"#eef4fa","strokeWidth":3,"strokeColor":"#101923"},"borderWidth":2,"scaling":{"min":12,"max":34}},
    "edges":{"arrows":{"to":{"enabled":true,"scaleFactor":0.65}},"color":{"color":"#71869a","highlight":"#f1cf79","hover":"#f1cf79"},"font":{"size":10,"color":"#d4dee8","strokeWidth":3,"strokeColor":"#101923","align":"middle"},"smooth":{"type":"dynamic"}},
    "physics":{"enabled":true,"solver":"forceAtlas2Based","forceAtlas2Based":{"gravitationalConstant":-48,"centralGravity":0.008,"springLength":145,"springConstant":0.08,"damping":0.45,"avoidOverlap":0.8},"stabilization":{"enabled":true,"iterations":250,"fit":true}},
    "interaction":{"hover":true,"navigationButtons":true,"keyboard":{"enabled":true},"tooltipDelay":120,"zoomView":true,"dragView":true}}
""")
for node in data.get("nodes",[]):
    props=node.get("properties") or {}
    title=escape("\n".join([f"{k}: {v}" for k,v in props.items()])) or node["id"]
    label=props.get("title") or props.get("name") or node["id"]
    if len(label)>56: label=label[:53]+"…"
    net.add_node(node["id"],label=label,title=title,group=node.get("type","Other"),color=COLORS.get(node.get("type"),"#9aa6b2"),shape="dot",size=24 if node.get("type")=="Work" else 16)
for edge in data.get("edges",[]):
    title=escape(str(edge.get("provenance") or ""))
    net.add_edge(edge["source"],edge["target"],label=edge.get("type",""),title=title)
# PyVis save_graph() uses the Windows ANSI code page on some systems;
# publication titles can contain characters that CP1251 cannot encode.
TARGET.write_text(net.generate_html(), encoding="utf-8")
print(f"Saved {TARGET}")
print("Open the HTML file in a browser. Hover for details; click a node to highlight its links.")


