import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

def find_top_3_cited_papers(session):
    result = session.run("""
        MATCH (p:Paper)-[:PUBLISHED_IN_VENUE]->(e:Edition)-[:BELONGS_TO]->(v:PublicationVenue)
        OPTIONAL MATCH (citingPaper:Paper)-[:CITES]->(p)
        WITH v.name AS venueName, p, count(citingPaper) AS citationCount
                         
        ORDER BY citationCount DESC
        WITH venueName, collect({paperID: p.paperID, title: p.title, citationCount: citationCount}) AS papers
        RETURN venueName, papers[0..3] AS top3CitedPapers
    """)
    for record in result:
        print(f"\nVenue: {record["venueName"]}")
        for paper in record["top3CitedPapers"]:
            print(f"Title: {paper["title"]}")
            print(f"Paper ID: {paper["paperID"]}")
            print(f"Citations: {paper["citationCount"]}")


def conference_workshop_communities(session):
    result = session.run("""
        MATCH (p:Paper)-[:PUBLISHED_IN_VENUE]->(e:Edition)-[:BELONGS_TO]->(v:PublicationVenue)
        MATCH (p)-[:WRITTEN_BY]->(a:Author)
        WITH v.name AS venueName, 
            a.name AS authorName, 
            collect(DISTINCT e.editionId) AS editions
                         
        WHERE size(editions) >= 2
        RETURN venueName, authorName, size(editions) AS numEditions
    """)
    for record in result:
        print(f"\nVenue: {record['venueName']}")
        print(f"Author: {record['authorName']}")
        print(f"Number of editions: {record['numEditions']}")


def impact_factor_journals(session):
    result = session.run("""
        MATCH (citing:Paper)-[:CITES]->(cited:Paper)
            -[:PUBLISHED_IN]->(v:Volume)
            -[:VOLUME_OF]->(j:Journal)
        WITH j, citing.year AS currentYear, COUNT(*) AS totalCitations
                         
        MATCH (paper1:Paper)-[:PUBLISHED_IN]->(v1:Volume)-[:VOLUME_OF]->(j)
        WHERE paper1.year = currentYear - 1
        WITH j, currentYear, totalCitations, COUNT(paper1) AS pubCountYminus1   

        MATCH (paper2:Paper)-[:PUBLISHED_IN]->(v2:Volume)-[:VOLUME_OF]->(j)
        WHERE paper2.year = currentYear - 2
        WITH j, 
            currentYear, 
            totalCitations, 
            pubCountYminus1, 
            COUNT(paper2) AS pubCountYminus2   
                         
        RETURN 
        j.name AS journal, 
        currentYear AS impactFactorYear,
        CASE 
            WHEN (pubCountYminus1 + pubCountYminus2) > 0 
            THEN (1.0 * totalCitations / (pubCountYminus1 + pubCountYminus2))
            ELSE 0
        END AS impactFactor
        ORDER BY journal, impactFactorYear;
    """)
    for record in result:
        print(f"{record['journal']} ({record['impactFactorYear']}): Impact Factor = {record['impactFactor']}")


def h_index_authors(session):
    result = session.run("""
        MATCH (p:Paper)-[:WRITTEN_BY]->(a:Author)
        OPTIONAL MATCH (citing:Paper)-[:CITES]->(p)
        RETURN a.name AS authorName, p.paperID AS paperID, COUNT(citing) AS citationCount
    """)

    author_citations = defaultdict(list)
    for record in result:
        author = record["authorName"]
        citation_count = record["citationCount"]
        author_citations[author].append(citation_count)

    for author, citations in author_citations.items():
        sorted_cites = sorted(citations, reverse=True)
        h_index = 0
        for i, c in enumerate(sorted_cites):
            if c >= i + 1:
                h_index += 1
            else:
                break
        print(f"{author} has h-index {h_index}")

def main():
    URI = os.getenv('URI')
    AUTH = (os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        print("Connection successful!")
        with driver.session(database="neo4j") as session:
            session.execute_write(find_top_3_cited_papers)
            #session.execute_write(conference_workshop_communities)
            #session.execute_write(impact_factor_journals)
            #session.execute_write(h_index_authors)

if __name__ == "__main__":
     main()