import requests
import time
import csv

# --- Configuration ---
SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"
# Add your API key or other configurations if needed

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

def extract_paper_details(paper):
    """
    Extract detailed information from a paper object.
    Expected details include title, abstract, authors, and citations.
    """
    doi = paper.get("externalIds", {}).get("DOI")
    journal = paper.get("journal", {})
    journal_name = journal.get("name") if journal else None
    pages = journal.get("pages") if journal else None
    abstract = paper.get("abstract")
    publicationVenue = paper.get("publicationVenue", {})
    publicationVenue_id = publicationVenue.get("id") if publicationVenue else None
    publicationVenue_name = publicationVenue.get("name") if publicationVenue else None
    title = paper.get("title")
    year = paper.get("year")
    list_of_authors = paper.get("authors") if paper.get("authors") else []
    list_of_fields = paper.get("s2FieldsOfStudy") if paper.get("s2FieldsOfStudy") else []

    author_ids = ";".join([author.get("authorId") for author in list_of_authors if author.get("authorId")])
    author_names = ";".join([author.get("name") for author in list_of_authors if author.get("name")])
    
    # Extract unique categories from list_of_fields
    categories = set([field.get("category") for field in list_of_fields if field.get("category")])
    fields = ";".join(categories)

    if not (doi and journal_name and pages and abstract and publicationVenue_id and publicationVenue_name and title and year):
        return None
    return {
        "paperID": paper.get("paperId"),
        "doi": doi,
        "journal_name": journal_name,
        "pages": pages,
        "abstract": abstract,
        "publicationVenue_id": publicationVenue_id,
        "publicationVenue_name": publicationVenue_name,
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
    with open('papers.csv', mode='w', newline='', encoding='utf-8',) as file:
        writer = csv.writer(file, delimiter="|")
        # Write the header
        writer.writerow([
            "paperID", "doi", "journal_name", "pages", "abstract", 
            "publicationVenue_id", "publicationVenue_name", "title", 
            "year", "authorIDs", "authorNames", "fields"
        ])
        # Write the paper details
        for paper_id, details in papers_db.items():
            writer.writerow([
                details["paperID"], details["doi"], details["journal_name"], 
                details["pages"], details["abstract"], details["publicationVenue_id"], 
                details["publicationVenue_name"], details["title"], details["year"], 
                details["authorIDs"], details["authorNames"], details["fields"]
            ])

# --- Main Process ---

def main():
    # Step 1: Bulk API call to retrieve paper data (limit ~1000)
    query_params = {
        "query": "machine learning",  # Example search query
        "fields": "title,externalIds,publicationVenue,year,s2FieldsOfStudy,journal,abstract,authors",
        "sort" : "citationCount:desc"
        # add other query parameters as needed
    }
    papers = get_bulk_paper_data(query_params)
    print(f"Retrieved {len(papers)} papers.")

    # Local databases (dictionaries) to store paper and author information
    papers_db = {}   # key: paper_id, value: details dict including authors & citations
    #authors_db = {}  # key: author_id, value: details dict

    # Step 2: Process each paper
    for paper in papers:
        paper_id = paper.get("paperId")
        paper_details = extract_paper_details(paper)
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