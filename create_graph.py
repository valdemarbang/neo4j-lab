from neo4j import GraphDatabase
from typing import List
from dotenv import load_dotenv
import os
import json

load_dotenv()

URI = os.getenv("URI")
AUTH = (os.getenv("USERNAME"), os.getenv("PASSWORD"))
QUERIES_PATH = os.getenv("QUERIES_PATH")

def parse_queries(queries_file: str) -> List[str]:
    """
    Parse the queries from the file and return a list of queries to create the graph
    """
    commands_list = []
    commands = open(queries_file, "r")
    line = commands.readline()
    curr_command = ""
    while line:
        if line == "\n" :
            commands_list.append(curr_command.strip())
            curr_command = ""
        else:
            curr_command += " " + line.strip("\n")
        line = commands.readline()
    return commands_list

def execute_queries(queries_list: List[str], driver: GraphDatabase.driver): 
    for query in commands_list:
        driver.execute_query(query, database_="neo4j")

if __name__ == "__main__":
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connection established.")
    commands_list = parse_queries(QUERIES_PATH)
    execute_queries(commands_list, driver)