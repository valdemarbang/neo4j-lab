import requests
import time
import csv
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
import json
from typing import List
import random

# --- Configuration ---
np.random.seed(42)

load_dotenv()
# Add your API key or other configurations if needed
SEMANTIC_SCHOLAR_BASE_URL = os.getenv('SEMANTIC_SCHOLAR_BASE_URL')
JOURNAL_NAMES = json.loads(os.getenv('JOURNAL_NAMES'))
ISSN_LIST = json.loads(os.getenv('ISSN_LIST'))
CONFERENCE_NAMES = json.loads(os.getenv('CONFERENCE_NAMES'))
WORKSHOP_NAMES = json.loads(os.getenv('WORKSHOP_NAMES'))
CITIES = json.loads(os.getenv('CITIES'))
LIST_AFF = json.loads(os.getenv('LIST_AFF'))
PROBA_APPROVE = float(os.getenv('PROBA_APPROVE'))

# --- Helper Functions ---

def get_bulk_paper_data(query_params):
    """
    Perform a bulk search call to the Semantic Scholar API to retrieve paper data.
    query_params should include any filters or limits (e.g., limit=100).
    Returns a list of paper data.
    """
    # Example endpoint: '/paper/search'
    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/paper/search/bulk"
    response = requests.get(url, params=query_params)
    if response.status_code == 200:
        data = response.json()
        # Assuming 'data' contains a list of papers under a key, e.g., 'data'
        papers = data.get('data', [])[:1000]
        return papers
    else:
        print("Error fetching bulk paper data:", response.status_code, response.text)
        return []

def generate_id(type: str, **kwargs) :
    if type == "journal" :
        issn = kwargs["issn"]
        volume = kwargs["volume"]
        return issn.replace(" ", "_") + "_" + str(volume)
    elif type == "venue" :
        name = kwargs["name"]
        city = kwargs["city"]
        year = kwargs["year"]
        return name.replace(" ", "_") + "_" + city.replace(" ", "_") + "_" + str(year)

def create_proceeding(rand: int) :
    if rand == 1 : # Conference
        conference_name = np.random.choice(CONFERENCE_NAMES)
        city = np.random.choice(CITIES)
        return conference_name, city
    else : # Workshop
        workshop_name = np.random.choice(WORKSHOP_NAMES)
        city = np.random.choice(CITIES)
        return workshop_name, city

def create_journal() :
    idx = np.random.randint(0, len(JOURNAL_NAMES))
    journal_name = JOURNAL_NAMES[idx]
    issn = ISSN_LIST[idx]
    volume = np.random.randint(1, 101)
    return journal_name, issn, volume

def get_random_citations(paper_id, paper_ids):
    available_ids = paper_ids[paper_ids != paper_id]  # Exclude the current paperId
    num_citations = np.random.randint(0, 21)  # Random number of citations (0 to 20)
    return ";".join(np.random.choice(available_ids, size=num_citations, replace=False).tolist())

def get_random_reviews(writer_ids, author_ids) :
    available_ids = author_ids[~author_ids.str.contains(writer_ids)]  # Exclude the writers ids
    flattened_ids = np.concatenate(np.char.split(list(available_ids), ";"))
    return ";".join(np.random.choice(flattened_ids, size=3, replace=False).tolist())

def generate_boolean_proba(p: float) -> bool :
    return np.random.random() < p

def create_reviews_approvements(p: float) -> List[str] :
    return ";".join([str(generate_boolean_proba(p)) for _ in range(3)])

def extract_paper_details(paper, number_papers):
    """
    Extract detailed information from a paper object.
    Expected details include title, abstract, authors, and citations.
    """
    # Randomly decide if the paper was published in a journal or a conference/workshop
    type_of_publication = np.random.randint(0, 3)
    if type_of_publication == 0 : # Journal
        journal_name, issn, volume = create_journal()
        volume_id = generate_id("journal", issn=issn, volume=volume)
    else :
        venue_name, city = create_proceeding(np.random.randint(1, 3))
        edition_id = generate_id("venue", name=venue_name, city=city, year=paper.get("year"))

    journal_name = journal_name if type_of_publication == 0 else None
    volume = volume if type_of_publication == 0 else None
    volume_id = volume_id if type_of_publication == 0 else None

    edition_id = edition_id if type_of_publication != 0 else None
    publicationVenue_name = venue_name if type_of_publication != 0 else None
    city_venue = city if type_of_publication != 0 else None

    doi = paper.get("externalIds", {}).get("DOI")
    journal = paper.get("journal", {})
    pages = journal.get("pages") if journal else None
    abstract = paper.get("abstract")
    title = paper.get("title")
    year = paper.get("year")
    list_of_authors = paper.get("authors") if paper.get("authors") else []
    list_of_fields = paper.get("s2FieldsOfStudy") if paper.get("s2FieldsOfStudy") else []

    author_ids = ";".join([author.get("authorId") for author in list_of_authors if author.get("authorId")])
    author_names = ";".join([author.get("name") for author in list_of_authors if author.get("name")])
    
    # Extract unique categories from list_of_fields
    categories = set([field.get("category") for field in list_of_fields if field.get("category")])
    fields = ";".join(categories)

    if not (doi and pages and abstract and title and year):
        return None
    return {
        "paperID": paper.get("paperId"),
        "doi": doi,
        "journal_name": journal_name,
        "volume": volume,
        "volume_id": volume_id,
        "pages": pages,
        "abstract": abstract,
        "publicationVenue_name": publicationVenue_name,
        "edition_id": edition_id,
        "city_venue": city_venue,
        "title": title,
        "year": year,
        "authorIDs": author_ids,
        "authorNames": author_names,
        "fields": fields
    }

"""def get_author_details(author_id):
    
    For a given author ID, retrieve detailed information about the author.
    
    # Example endpoint: '/author/{author_id}'
    fields = "name,affiliations,homepage,publicationCount"
    url = f"{SEMANTIC_SCHOLAR_BASE_URL}/author/{author_id}"
    response = requests.get(url, params={"fields": fields})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching details for author {author_id}:", response.status_code, response.text)
        return None
"""

def export_to_neo4j(papers_db):
    """
    Export the gathered data to Neo4j.
    This could be done by:
      - Exporting CSVs for nodes (papers and authors) and relationships (e.g., paper cites paper, author wrote paper)
      - OR using a Neo4j driver (like neo4j or py2neo) to create nodes and relationships directly.
    """
    # Export papers to CSV
    with open('./csv/papers_venues.csv', mode='w', newline='', encoding='utf-8',) as file:
        writer = csv.writer(file, delimiter="|")
        # Write the header
        writer.writerow([
            "paperID", "doi", "journal_name", "volume", "volume_id", "pages", "abstract", 
            "publicationVenue_name", "edition_id", "city_venue", "title", 
            "year", "authorIDs", "authorNames", "fields"
        ])
        # Write the paper details
        for paper_id, details in papers_db.items():
            writer.writerow([
                details["paperID"], details["doi"], details["journal_name"], details["volume"],
                details["volume_id"], details["pages"], details["abstract"],
                details["publicationVenue_name"], details["edition_id"], details["city_venue"],
                details["title"], details["year"], details["authorIDs"], 
                details["authorNames"], details["fields"]
            ])
    #Create random citation links from the list of papers
    df = pd.read_csv('./csv/papers_venues.csv', delimiter='|')
    df['citedPaperID'] = df['paperID'].apply(lambda x: get_random_citations(x, df['paperID'].values))

    #Create random reviews links from the list of authors
    df['reviewerIDs'] = df['authorIDs'].apply(lambda x: get_random_reviews(x, df['authorIDs']))
    #reviews_approvements = create_reviews_approvements(PROBA_APPROVE)
    df['reviewsApprovements'] = df['paperID'].apply(lambda x: create_reviews_approvements(PROBA_APPROVE))
    df["reviewsDesc"] = "desc;desc;desc"

    # Create random affiliations for authors
    unique_author_ids = list(set(";".join(list(df['authorIDs'])).split(";")))
    author_affiliations = np.random.choice(LIST_AFF, size=len(unique_author_ids), replace=True)
    df_aff = pd.DataFrame({'authorID': unique_author_ids, 'affiliation': author_affiliations})
    df_aff.to_csv('./csv/authors_affiliations.csv', index=False, sep='|')

    # Export the updated data to CSV
    df.to_csv('./csv/papers_venues.csv', index=False, sep='|')


# --- Main Process ---

def main():
    # Step 1: Bulk API call to retrieve paper data (limit ~1000)
    query_params = {
        "query": "machine learning",  # Example search query
        "fields": "title,journal,externalIds,year,s2FieldsOfStudy,abstract,authors",
        "sort" : "citationCount:desc"
        # add other query parameters as needed
    }
    papers = get_bulk_paper_data(query_params)
    number_papers = len(papers)
    print(f"Retrieved {number_papers} papers.")

    # Local databases (dictionaries) to store paper and author information
    papers_db = {}   # key: paper_id, value: details dict including authors & citations
    #authors_db = {}  # key: author_id, value: details dict

    # Step 2: Process each paper
    for paper in papers:
        paper_id = paper.get("paperId")
        paper_details = extract_paper_details(paper, number_papers)
        if paper_details is None:
            continue  # Skip papers that encountered an error
        papers_db[paper_id] = paper_details

        # Process authors for the paper
        
    # Now you have:
    # - papers_db: a dictionary with detailed info for all papers (including citations)
    # - authors_db: a dictionary with detailed info for all authors
    print(f"Total papers gathered: {len(papers_db)}")

    # Step 4: Export the data to Neo4j
    export_to_neo4j(papers_db)
    print("Exported data to Neo4j.")

if __name__ == "__main__":
    main()