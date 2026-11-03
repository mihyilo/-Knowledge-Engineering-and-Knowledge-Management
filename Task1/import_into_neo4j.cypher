// Run this in Neo4j Desktop > Query after copying the five CSVs into the DBMS import folder.
CREATE CONSTRAINT work_id IF NOT EXISTS FOR (n:Work) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT person_id IF NOT EXISTS FOR (n:Person) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT venue_id IF NOT EXISTS FOR (n:Venue) REQUIRE n.id IS UNIQUE;

LOAD CSV WITH HEADERS FROM 'file:///works.csv' AS row
MERGE (n:Work {id: row.id})
SET n.title = row.title, n.doi = row.doi, n.year = toInteger(row.year), n.source_url = row.source_url;

LOAD CSV WITH HEADERS FROM 'file:///people.csv' AS row
MERGE (n:Person {id: row.id})
SET n.name = row.name;

LOAD CSV WITH HEADERS FROM 'file:///venues.csv' AS row
MERGE (n:Venue {id: row.id})
SET n.name = row.name;

LOAD CSV WITH HEADERS FROM 'file:///authored_by.csv' AS row
MATCH (w:Work {id: row.start_id}), (p:Person {id: row.end_id})
MERGE (w)-[r:AUTHORED_BY]->(p)
SET r.provenance = row.provenance;

LOAD CSV WITH HEADERS FROM 'file:///published_in.csv' AS row
MATCH (w:Work {id: row.start_id}), (v:Venue {id: row.end_id})
MERGE (w)-[r:PUBLISHED_IN]->(v)
SET r.provenance = row.provenance;
