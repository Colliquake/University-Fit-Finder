from pymongo import MongoClient
import pandas as pd
import os
from dotenv import load_dotenv

# Load variables from .env into the system environment
load_dotenv()

client = MongoClient(f"{os.getenv('MONGO_HOST')}")
db = client[f"{os.getenv('MONGO_DB')}"]

def create_indexes():
    # Create indexes to speed up the query
    # Create these every time (MongoDB will skip these automatically if they already exist)
    db.faculty.create_index("affiliation.name")
    db.faculty.create_index("publications")
    db.publications.create_index("id")
    db.publications.create_index("year")
    db.publications.create_index("numCitations")

def get_all_universities():

    create_indexes()

    universities = db.faculty.distinct("affiliation.name")
    return sorted(universities)

def get_university_citation_trends(universities):

    create_indexes()

    query = [
        {"$match": {"affiliation.name": {"$in": universities}}},
        {"$project": {"affiliation.name": 1, "publications": 1}},
        {"$unwind": "$publications"},
        {"$lookup": {
            "from": "publications",
            "let": {"pub_id": "$publications"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {"$eq": ["$id", "$$pub_id"]},
                        "year": {"$gt": 0, "$lt": 2027}
                    }
                },
                {"$project": {"year": 1, "numCitations": 1}}
            ],
            "as": "publication"}
        },
        {"$unwind": "$publication"},
        {"$group": {
            "_id": {
                "university": "$affiliation.name",
                "year": "$publication.year"
            },
            "totalCitations": {"$sum": "$publication.numCitations"}}
        },
        {"$project": {"_id": 0, "university": "$_id.university", "year": "$_id.year", "totalCitations": 1}},
        {"$sort": {"university": 1, "year": 1}}
    ]
    results = db.faculty.aggregate(query)
    return pd.DataFrame(list(results))

# print(get_citation_trends(["Cornell University", "University of Michigan"]))
# print(get_all_universities())
