from neo4j import GraphDatabase
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()

def delete_all_nodes(session):
    session.run("MATCH (n) DETACH DELETE n")

def load_raw_papers(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS r 
        FIELDTERMINATOR '|' 
        CREATE (p:Papers) 
        SET p = r
    """)

def create_papers(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        CREATE (p:Paper {
            paperID: row.paperID,
            title: row.title,
            year: toInteger(row.year),
            abstract: row.abstract,
            pages: row.pages,
            doi: row.doi
        })
    """)

def create_authors(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row, split(row.authorIDs, ';') AS authorIDs, split(row.authorNames, ';') AS authorNames
        UNWIND range(0, size(authorIDs) - 1) AS i
        MERGE (a:Author {authorID: authorIDs[i], name: authorNames[i]})
    """)

def create_fields(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row, split(row.fields, ';') AS fields
        UNWIND fields AS field
        MERGE (f:Field {name: field})
    """)

def create_journals(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row
        WHERE row.journal_name IS NOT NULL AND row.journal_name <> ''
        MERGE (:Journal {name: row.journal_name})
    """)

def create_venues(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row
        WHERE row.publicationVenue_name IS NOT NULL AND row.publicationVenue_name <> ''
        MERGE (:PublicationVenue {name: row.publicationVenue_name})
    """)

def create_volumes(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row
        WHERE row.volume_id IS NOT NULL AND row.volume_id <> ''
          AND row.volume IS NOT NULL AND row.volume <> ''
        MERGE (vo:Volume {volumeId: row.volume_id, volume: row.volume})
    """)

def create_editions(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row
        WHERE row.edition_id IS NOT NULL AND row.edition_id <> ''
          AND row.city_venue IS NOT NULL AND row.city_venue <> ''
        MERGE (e:Edition {editionId: row.edition_id, city: row.city_venue})
    """)
def create_written_by_relationships(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row, split(row.authorIDs, ';') AS authorIDs
        MATCH (p:Paper {paperID: row.paperID})
        UNWIND authorIDs AS authorID
        MATCH (a:Author {authorID: authorID})
        CREATE (p)-[:WRITTEN_BY]->(a)
    """)

def create_in_field_relationships(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row, split(row.fields, ';') AS fields
        MATCH (p:Paper {paperID: row.paperID})
        UNWIND fields AS field
        MATCH (f:Field {name: field})
        CREATE (p)-[:IN_FIELD]->(f)
    """)

def create_published_in_volume(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        MATCH (p:Paper {paperID: row.paperID})
        MATCH (vo:Volume {volumeId: row.volume_id})
        CREATE (p)-[:PUBLISHED_IN]->(vo)
    """)

def create_published_in_edition(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        MATCH (p:Paper {paperID: row.paperID})
        MATCH (e:Edition {editionId: row.edition_id})
        CREATE (p)-[:PUBLISHED_IN_VENUE]->(e)
    """)

def create_volume_of_relationship(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        MATCH (j:Journal {name: row.journal_name})
        MATCH (vo:Volume {volumeId: row.volume_id})
        CREATE (vo)-[:VOLUME_OF]->(j)
    """)

def create_edition_belongs_to_venue(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        MATCH (v:PublicationVenue {name: row.publicationVenue_name})
        MATCH (e:Edition {editionId: row.edition_id})
        CREATE (e)-[:BELONGS_TO]->(v)
    """)

def create_affiliations(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///authors_affiliations.csv' AS row
        FIELDTERMINATOR '|'
        MERGE (f:Affiliation {affiliation: row.affiliation})
    """)

def link_authors_to_affiliations(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///authors_affiliations.csv' AS row
        FIELDTERMINATOR '|'
        MATCH (a:Author {authorID: row.authorID})
        MATCH (f:Affiliation {affiliation: row.affiliation})
        CREATE (a)-[:AFFILIATED_TO]->(f)
    """)

def create_citations(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row, split(row.citedPaperID, ';') AS citedIDs
        MATCH (p:Paper {paperID: row.paperID})
        UNWIND citedIDs AS citedID
        MATCH (c:Paper {paperID: citedID})
        CREATE (p)-[:CITES]->(c)
    """)

def create_reviews(session):
    session.run("""
        LOAD CSV WITH HEADERS FROM 'file:///papers_venues.csv' AS row
        FIELDTERMINATOR '|'
        WITH row, split(row.reviewerIDs, ';') AS reviewerIDs, split(row.reviewsApprovements, ';') AS reviewsApprovements, split(row.reviewsDesc, ';') AS reviewsDesc
        MATCH (p:Paper {paperID: row.paperID})
        UNWIND range(0, size(reviewerIDs) - 1) AS i
        MATCH (a:Author {authorID: reviewerIDs[i]})
        CREATE (p)-[:REVIEWED_BY {reviewApprovement: reviewsApprovements[i], reviewDesc: reviewsDesc[i]}]->(a)
    """)


def main():
    URI = os.getenv('URI')
    AUTH = (os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))

    print("Dont forget to add the CSV files to the graph database!")

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        print("Connection successful!")
        with driver.session(database="neo4j") as session:
            session.execute_write(delete_all_nodes)
            print('Creating and loading the nodes and relationships into the database...')

            session.execute_write(load_raw_papers)
            session.execute_write(create_papers)
            session.execute_write(create_authors)
            session.execute_write(create_fields)
            session.execute_write(create_journals)
            session.execute_write(create_venues)
            session.execute_write(create_volumes)
            session.execute_write(create_editions)
            session.execute_write(create_written_by_relationships)
            session.execute_write(create_in_field_relationships)
            session.execute_write(create_published_in_volume)
            session.execute_write(create_published_in_edition)
            session.execute_write(create_volume_of_relationship)
            session.execute_write(create_edition_belongs_to_venue)
            session.execute_write(create_affiliations)
            session.execute_write(link_authors_to_affiliations)
            session.execute_write(create_citations)
            session.execute_write(create_reviews)

            print('Creation and loading done for the database.')

if __name__ == "__main__":
     main()