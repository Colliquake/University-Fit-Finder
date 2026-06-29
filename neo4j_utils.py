from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load variables from .env into the system environment
load_dotenv()

driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD')))
driver.verify_connectivity()

def get_related_professors(name):
    with driver.session(database="academicworld") as session:
        result = session.run("""
            MATCH (f:FACULTY {name: $name})-[:INTERESTED_IN]->(k:KEYWORD)<-[:INTERESTED_IN]-(f2:FACULTY)
            WHERE f2.name <> $name
            RETURN f2.name AS Professor,
                COUNT(k) AS SharedKeywords
            ORDER BY SharedKeywords DESC
            LIMIT 10
        """, name=name)
        return [node.data() for node in result]

# def get_professors_by_keywords(keywords):
#     with driver.session(database="academicworld") as session:
#         result = session.run("""
#             MATCH (f:FACULTY)-[:INTERESTED_IN]->(k:KEYWORD)
#             WHERE k.name IN $keywords
#             RETURN f.name AS Professor,
#                 COUNT(k) AS MatchedKeywords
#             ORDER BY MatchedKeywords DESC
#             LIMIT 20
#         """, keywords=keywords)
#         return [node.data() for node in result]

def get_professors_by_keywords(keywords):
    with driver.session(database="academicworld") as session:
        result = session.run("""
            MATCH (f:FACULTY)-[:INTERESTED_IN]->(k:KEYWORD)
            WHERE toLower(k.name) IN $keywords
            RETURN f.name AS Professor,
                COUNT(k) AS MatchedKeywords
            ORDER BY MatchedKeywords DESC
        """, keywords=[k.lower() for k in keywords])
        return [record.data() for record in result]