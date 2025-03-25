import os
from neo4j import GraphDatabase

def find_top_3_cited_papers(session):
    pass

def conference_workshop_communities(session):
    pass

def impact_factor_journals(session):
    pass

def h_index_authors(session):
    pass


def main():
    URI = os.getenv('URI')
    AUTH = (os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        print("Connection successful!")
        with driver.session(database="neo4j") as session:
            session.execute_write(find_top_3_cited_papers)
            session.execute_write(conference_workshop_communities)
            session.execute_write(impact_factor_journals)
            session.execute_write(h_index_authors)

if __name__ == "__main__":
     main()