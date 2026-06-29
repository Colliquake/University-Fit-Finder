import pandas as pd
import os
from sqlalchemy import create_engine, inspect, Table, Column, MetaData, Integer, Float, text, func
from sqlalchemy.dialects.mysql import insert
from dotenv import load_dotenv
import html
import re

# Load variables from .env into the system environment
load_dotenv()

engine = create_engine(f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}")
inspector = inspect(engine)

PRE_IMG = '<img src="'
POST_IMG = '" width="125px" height="75px"/>'

def get_universities_list():
    query = f"""
    SELECT
        u.id,
        u.name as University,
        CONCAT(CONCAT('{PRE_IMG}', u.photo_url), '{POST_IMG}') as Photo,
        COUNT(DISTINCT p.id) 'Number of Publications',
        SUM(p.num_citations) 'Total Citations',
        AVG(p.num_citations) 'Citations per Publication',
        top_interests.research_interest 'Top Research Interest',
        'FOLLOW' as Follow
    FROM publication p 
    JOIN faculty_publication fp ON fp.publication_Id = p.ID
    JOIN faculty f ON fp.faculty_Id = f.id
    JOIN university u on u.id = f.university_id
    LEFT JOIN (
        SELECT
            university_id,
            research_interest
        FROM ( SELECT
                f.university_id,
                f.research_interest,
                ROW_NUMBER() OVER (
                    PARTITION BY f.university_id
                    ORDER BY COUNT(*) DESC
                ) AS rn
            FROM faculty f
            WHERE f.research_interest != ''
            GROUP BY f.university_id, f.research_interest
        ) as top_interests
        WHERE rn = 1
    ) AS top_interests ON top_interests.university_id = u.id
    GROUP BY u.id, u.name, u.photo_url, top_interests.research_interest
    ORDER BY u.name;
    """
    df = pd.read_sql(query, con=engine)
    return df

def get_or_create_favorite_universities():

    def create_table_and_view():
        # Create the favorite_universities table
        meta = MetaData()
        favorite_universities = Table(
            'favorite_universities',
            meta,
            Column('university_id', Integer, primary_key=True),
            Column('rating', Float)
        )
        favorite_universities.create(engine, checkfirst=True)

        # Create the favorite_universities_view that joins in the university information.
        # This join view is created so that we don't duplicate data by adding university name and photo url to the
        # favorite_universities table.
        query = """
            CREATE OR REPLACE VIEW favorite_universities_view AS
            SELECT fu.university_id, fu.rating, u.name, u.photo_url
            FROM favorite_universities fu
            JOIN university u ON fu.university_id = u.id;
            """
        with engine.begin() as conn:
            conn.execute(text(query))
            conn.commit()

    if not inspector.has_table("favorite_universities"):
        create_table_and_view()

    query = f"""
    SELECT 
        university_id, 
        rating, 
        name as University, 
        CONCAT(CONCAT('{PRE_IMG}', photo_url), '{POST_IMG}') as Photo
    FROM favorite_universities_view
    ORDER BY rating DESC;
    """
    df = pd.read_sql(query, con=engine)
    return df

def upsert_favorite_university(university_id, rating=0.0):
    with engine.connect() as conn:
        metadata = MetaData()
        favorites = Table("favorite_universities", metadata, autoload_with=engine)
        insrt = insert(favorites).values(university_id=university_id, rating=rating)
        upsert = insrt.on_duplicate_key_update(rating=insrt.inserted.rating)
        conn.execute(upsert)
        conn.commit()

def clean_research_interests(val):
    if not isinstance(val, str) or val.strip() == '':
        return 'N/A'
    
    val = re.sub(r'(?i)^[\s\W]*interests\s*:\s*', '', val).strip()
    val = val.replace('&amp;', ';')
    val = val.replace(',', ';')
    val = re.sub(r'\s*;\s*', '; ', val).strip()
    val = ' '.join(word[0].upper() + word[1:] if word else word for word in val.split())

    return val

def get_professors_list():
    with engine.connect() as conn:
        conn.execute(text("""
            PREPARE get_professors_list FROM '
                SELECT
                    fu.id,
                    fu.name AS Professor,
                    CAST(fu.research_interest AS CHAR) AS ''Research Interests'',
                    fu.affiliation AS ''Affiliation'',
                    SUM(p.num_citations) AS ''Total Citations''
                FROM (
                    SELECT
                        fu.id,
                        fu.name,
                        fu.research_interest,
                        fu.affiliation,
                        fp.publication_Id
                    FROM (
                        SELECT
                            f.id,
                            f.name,
                            f.research_interest,
                            u.name AS affiliation
                        FROM
                            faculty f,
                            university u
                        WHERE
                            f.university_id = u.id
                        ) fu,
                        faculty_publication fp
                    WHERE fu.id = fp.faculty_Id
                    ) fu,
                    publication p
                WHERE
                    fu.publication_Id = p.ID
                GROUP BY fu.id
                ORDER BY SUM(p.num_citations) DESC
            '
        """))
        result = conn.execute(text("EXECUTE get_professors_list"))
        rows = result.fetchall()
        cols = result.keys()
        conn.execute(text("DEALLOCATE PREPARE get_professors_list"))

    df = pd.DataFrame(rows, columns=cols)
    df['Research Interests'] = df['Research Interests'].apply(clean_research_interests)

    df['Show More'] = 'Show More'
    df['Follow'] = 'Follow'

    return df

def get_professor_details(professor_name):
    with engine.connect() as conn:
        conn.execute(text("""
            SET @stmt = '
                SELECT
                    p.title AS Title,
                    p.year AS ''Publication Year'',
                    p.num_citations AS ''Number of Citations'',
                    GROUP_CONCAT(k.name SEPARATOR ''; '') AS ''Keywords''
                FROM
                    keyword k,
                    publication p,
                    publication_keyword pk,
                    faculty_publication fp,
                    faculty f
                WHERE
                    f.name LIKE ?
                    AND fp.faculty_id = f.id
                    AND fp.publication_id = p.id
                    AND pk.publication_id = p.id
                    AND k.id = pk.keyword_id
                GROUP BY
                    p.id, p.title, p.year, p.num_citations
                ORDER BY
                    p.year ASC
            '
        """))
        conn.execute(text("PREPARE get_professor_details FROM @stmt"))
        conn.execute(text("SET @name = :name"), {"name": f"%{professor_name}%"})
        result = conn.execute(text("EXECUTE get_professor_details USING @name"))
        rows = result.fetchall()
        cols = result.keys()
        conn.execute(text("DEALLOCATE PREPARE get_professor_details"))

    return pd.DataFrame(rows, columns=cols)

def get_professor_keyword_trends(professor_name):
    with engine.connect() as conn:
        conn.execute(text("""
            SET @stmt = '
                SELECT
                    p.year,
                    k.name AS keyword,
                    COUNT(*) AS count
                FROM
                    keyword k,
                    publication p,
                    publication_keyword pk,
                    faculty_publication fp,
                    faculty f
                WHERE
                    f.name LIKE ?
                    AND fp.faculty_id = f.id
                    AND fp.publication_id = p.id
                    AND pk.publication_id = p.id
                    AND k.id = pk.keyword_id
                GROUP BY
                    p.year,
                    k.name
                ORDER BY
                    p.year
            '
        """))
        conn.execute(text("PREPARE get_professor_keyword_trends FROM @stmt"))
        conn.execute(text("SET @name = :name"), {"name": f"%{professor_name}%"})
        result = conn.execute(text("EXECUTE get_professor_keyword_trends USING @name"))
        rows = result.fetchall()
        cols = result.keys()
        conn.execute(text("DEALLOCATE PREPARE get_professor_keyword_trends"))

    return pd.DataFrame(rows, columns=cols)

def upsert_favorite_professor(professor_id, rating=None):
    with engine.connect() as conn:
        metadata = MetaData()
        favorites = Table("favorite_faculty", metadata, autoload_with=engine)
        insrt = insert(favorites).values(faculty_id=professor_id, rating=rating)
        upsert = insrt.on_duplicate_key_update(rating=func.coalesce(insrt.inserted.rating, favorites.c.rating))
        conn.execute(upsert)
        conn.commit()

def get_or_create_favorite_professors():

    def create_table_and_view():
        # Create the favorite_faculty table
        meta = MetaData()
        favorite_faculty = Table(
            'favorite_faculty',
            meta,
            Column('faculty_id', Integer, primary_key=True),
            Column('rating', Float)
        )
        favorite_faculty.create(engine, checkfirst=True)

        query = """
            CREATE OR REPLACE VIEW favorite_faculty_view AS
            SELECT ff.faculty_id, f.name, f.research_interest, u.name AS Affiliation, ff.rating
            FROM favorite_faculty ff
            JOIN faculty f ON ff.faculty_id = f.id
            JOIN university u ON f.university_id = u.id
            """
        with engine.begin() as conn:
            conn.execute(text(query))
            conn.commit()

    if not inspector.has_table("favorite_faculty"):
        create_table_and_view()

    query = f"""
    SELECT 
        faculty_id,
        rating,
        name as Professor,
        research_interest AS 'Research Interests',
        affiliation AS Affiliation
    FROM favorite_faculty_view
    ORDER BY rating DESC;
    """
    df = pd.read_sql(query, con=engine)

    df['Remove'] = 'Remove'

    return df

def delete_favorite_professor(id):
    with engine.connect() as conn:
        metadata = MetaData()
        favorites = Table("favorite_faculty", metadata, autoload_with=engine)
        conn.execute(favorites.delete().where(favorites.c.faculty_id == id))
        conn.commit()

# print(get_or_create_favorite_universities())
# upsert_favorite_university(1211,2.0)
# print(get_or_create_favorite_universities())

# print(inspector.has_table("favorite_universities"))
# print(get_or_create_favorite_universities())
# print(inspector.has_table("favorite_universities"))

# TODO: DO NOT USE, we are doing citation trends in MongoDB, this was just for testing purposes, leaving this here for reference
# def get_citation_trends(universities):
#     query = f"""
#     SELECT
#         u.id,
#         u.name as university_name,
#         u.photo_url,
#         p.year,
#         SUM(p.num_citations) tot_citations
#     FROM publication p
#     JOIN faculty_publication fp ON fp.publication_Id = p.ID
#     JOIN faculty f ON fp.faculty_Id = f.id
#     JOIN university u on u.id = f.university_id
#     WHERE u.name in {tuple(universities)} AND p.year > 0 AND p.year < 2027
#     GROUP BY u.id, u.name, u.photo_url, p.year
#     ORDER BY u.id, year;
#     """
#     df = pd.read_sql(query, con=engine)
#     return df