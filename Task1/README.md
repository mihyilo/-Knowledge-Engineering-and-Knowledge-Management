# Task 1: Knowledge Graph

## Requirements

- Python 3.10 or newer. Building the graph uses only the Python standard library.
- Neo4j Desktop with a local DBMS to import and query the graph.
- Optional: install PyVis to generate the interactive browser visualization:

```powershell
python -m pip install pyvis
```

## Build the graph

From the `Task1` directory, run:

```powershell
python build_graph.py
```

The script reads `works.csv` and `abstracts.csv`, builds the graph data, and writes the Neo4j CSV files to `neo4j_import/`. The five files used by the Neo4j import are `works.csv`, `people.csv`, `venues.csv`, `authored_by.csv`, and `published_in.csv`.

To collect a fresh publication sample first, run the fetcher (this replaces `works.csv` and `abstracts.csv`):

```powershell
python fetch_openalex.py --query "graph data integration" --from-year 2018 --to-year 2025 --limit 100
```

OpenAlex supports basic searches without an API key. To use a key, set `OPENALEX_API_KEY` before fetching.

## Interactive graph

Install the optional PyVis dependency, then run:

```powershell
python plot_interactive.py
```

Open `output/knowledge_graph_interactive.html` in a browser.

## Import into Neo4j Desktop

1. Run `python build_graph.py` to create or refresh the CSV files in `neo4j_import/`.
2. In Desktop, open your local DBMS menu and choose **Open folder**.
3. Create an `import` folder if it does not exist. Copy the five CSV files from `neo4j_import/` into that folder.
4. Start the DBMS and open **Query**.
5. Open `import_into_neo4j.cypher` and run its statements.
6. Run the example queries below in the same Query window.

The Cypher script uses `LOAD CSV` with `file:///`, so Neo4j reads the files from that DBMS's `import` folder.

## Example graph queries

Run these queries after importing the graph into Neo4j.

```cypher
// 1. Works by author
MATCH (w:Work)-[:AUTHORED_BY]->(p:Person {name: 'Ana-Maria Ghiran'})
RETURN w.title, w.doi, w.year;

// 2. Number of works by year
MATCH (w:Work)
RETURN w.year AS year, count(w) AS works
ORDER BY year;

// 3. Number of works by venue
MATCH (w:Work)-[:PUBLISHED_IN]->(v:Venue)
RETURN v.name AS venue, count(w) AS works
ORDER BY works DESC;

// 4. Different authors whose separate works share a venue
MATCH (p1:Person)<-[:AUTHORED_BY]-(w1:Work)-[:PUBLISHED_IN]->(v:Venue)
      <-[:PUBLISHED_IN]-(w2:Work)-[:AUTHORED_BY]->(p2:Person)
WHERE w1.id <> w2.id AND p1.id < p2.id
RETURN p1.name AS author_1,
       p2.name AS author_2,
       v.name AS venue,
       w1.id AS work_1_id,
       w1.title AS work_1,
       w2.id AS work_2_id,
       w2.title AS work_2
ORDER BY venue, author_1, author_2, work_1;
```

Q4 returns pairs of different authors whose separate works share a venue. A shared venue alone does not establish co-authorship or collaboration. Save the query and its returned rows with the Task 1 results.
