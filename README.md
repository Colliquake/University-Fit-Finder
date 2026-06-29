# University Fit-Finder

## Purpose

University Fit-Finder is an application to help students applying to universities to discover universities that fit them best.

Students are able to examine faculty and universities and if their research interests align, examine the reputation of universities through citation counts, and find related professors at other schools to ones they like. Among other functions in the app.

Target users are high school students applying to undergraduate programs or anyone looking to apply for a graduate program at a university. These target users are more researched focused as the app focuses on metrics for reasearch such as citations, as well as what faculty focuses on what research topics.

The final objective of the app is to allow users to create a final list of "followed" universities they would apply to 
and "followed" professors they would like to research with or take classes from.

This app is useful in that it helps students assess universities and professorss quantitatively and discover new universities and professors they may not have found otherwise. 
It also allows students to build a personalized list of universities they are interested in and easily access information about them. This will lead them to make a more informed 
decision about which university to apply to and attend.

The app is also cool because it puts all of this data in one place. Typically students must invest a lot of time researching universities and professors across many different websites and platforms. 
This app puts all of this data in one place and makes it easy to access and understand with nice visuals. Not only does this
help with research but it uniquely allows students to build their own list of universities and professors they are interested in to track their university application research.

## Demo
- [Link](https://mediaspace.illinois.edu/media/t/1_cp8baqgs)
- Demo video is also sent through chatroom in case video does not finish processing

## Installation

Before installing the app, please have the MongoDB, MySQL and Neo4J databases running from the class MPs.

1. Clone this repo.
   
2. Install the required libraries: 
```
pip install -r requirements.txt
```

3. Then copy the `.env-sample` file to `.env` and fill in the database credentials. 
This file should not be checked into git, it contains your personal database credentials.

4. From the repo root, run the app with this command: `python app.py`

Navigate to http://127.0.0.1:8050/ to see the dashboard.

The app will take a few seconds to start up and then a few more seconds (up to 10) to load the webpage as it runs the initial 
queries to populate the widgets.

## Usage
Browse through the universities to view the metrics grouped by universities. These metrics include number of publications, number of citations, average citations per publication, and the top research topic at that university. Filter by university name and/or by the top research topic. Click on the Follow button to add the university to your personal list of followed universities.

In your list of followed universities, double-click on the rating number for a university to change your personal score for said university. Universities are by default sorted by their rating scores in descending order.

To view the number of citations a university has as a trend, select the university from the University Citations Per Year section. Select multiple universities at once to compare them.

All the faculty are displayed in a grid in the Professors widget, sorted by their total citations in descending order. Filter through faculty via their names, research interests, affiliation, and total citations count. To view more information about a faculty, click the Show More button. To follow a faculty, click the Follow button.

Clicking the Follow button for a faculty adds them to your personal list of followed professors. It automatically displays the professor's name, research interests, and their affiliation. Double-click their rating score to change your personal score for said faculty on a scale of 0-5. Professors are by default sorted by your rating scores. Click on the Remove button for a professor to remove them from your list.

Clicking on the Show More button for a professor reveals another widget. This widget displays the professors name, affiliation, research interests, and all of their publications information (publication title, year, number of citations, and keywords). It also displays the professor's top 20 keyword trends over time. This gives a general idea of how a professor's research interests changed (or didn't!) over time. Click the Close button (near the top right of this widget) to close the detailed view.

Find professors that most closely match the keywords you are most interested in. Enter keywords separated by commas, and press the Search button to see which professors most closely match your keywords. Professors are sorted in descending order based on how many keywords match.

If you see a professor from this list and want to view other professors that closely match your professor of interest, select their row. This reveals other Related Professors, and how many keywords they have in common with your professor of interest.

## Design
The dashboard is designed to contain six total widgets. Three widgets relating to universities and three widgets relating to professors.

The three university widgets are:
1. **University List:** shows a list of universities with the total number of publications produced by faculty associated 
with that university, the total number of citations those publications have, the average number of citations per paper, 
the top research interests among the faculty at that university,
and a follow button to add the university to the followed universities list. The university list can be sorted by each column. 
The list can also be queried by university name to make it easier to find specific universities and by
"Top Research Interests" to find universities that align with the user's research interests. This widget is
backed by MySQL.
   - Note: the research interests column in the underlying database was not very clean so some odd entries may appear in
   the top research interests column. We did not clean this data but this is an area for future improvement.
2. **Followed Universities:** shows a list of universities the user has followed and an
editable rating column rate how much they like the university. Double-click on the row to edit the rating. 
This rating is persisted to the new `favorite_universities` table in the database which also contains the university_id 
of each followed university. The list is automatically sorted by this rating and a filter option allows 
the user to view only universities above a certain rating. This widget is backed by MySQL with a view 
to join university name and university photo to the `favorite_universities` table.
3. **Citation Trends:** shows the number of citations per year for a set of universities. A dropdown allows the user to 
select one or more universities to compare against. This widgets is backed by MongoDB with Indexes to speed up this 
large aggregation query.

The three professor widgets are:

4. **Professor List:** shows a list of professors with their names, research interests, affiliation, and total number of citations. It also has a Show More and a Follow button. Clicking on Show More reveals more information about the professor, including their publications, and their top 20 keyword trends over time. This widget is backed by MySQL, with prepared statements for use when clicking the Show More buttons.

5. **Followed Professors:** shows a list of professors the user has followed and an editable rating column, similar to the followed universities widget. A new followed_faculty table is added to the MySQL database that stores the user's rating and faculty_id. This is backed by MySQL.
   
6. **Related Keywords and Professors:** given a list of user's research interest keywords, shows a list of professors that match their keywords, sorted in descending order by the number of matched keywords. Clicking on a professor shows the related professors, sorted in descending order by the number of shared keywords. This widget is backed by Neo4j.

## Implementation
The front end of the dashboard was implemented in Python using the Dash Plotly framework. dash_bootstrap_components, dash_ag_grid, and plotly express
were also used as add-ons to the dash framework for additional functionality. A custom javascript button was also created
in order to embed a button within the dash ag grid for the Follow buttons in the university and professor lists, as 
well as the Show More button in the professor list.

The backend databases used were MySQL, MongoDB, and Neo4j.
To interface with these backend databases, we used the follow libraries:
- sqlalchemy for MySQL
- pymongo for MongoDB
- neo4j Python driver for Neo4j

Pandas was also used to easily facilitate data retrieval from the databases as it interfaced well with dash.

A central `app.py` file contains dash plotly code to control the user interface and facilitate widget interaction with a 
database. Callbacks are used to link user interactions with the database queries and to update the widgets with new data
from the database. These callbacks use several utils files define in `mysql_utils.py`, `mongodb_utils.py`, and `neo4j_utils.py`
to interact with the databases and run the necessary queries. These utils files contain logic for connecting to the databases
and running queries for with the different query languages for each database.

Finally, a `.env` file is used to store database credentials and other environment variables. We used the python-dotenv 
library to load these environment variables into our app at runtime.

## Database Techniques
- **Indexing**: Used in the MongoDB query to get the number of citations per year for a set of universities. 
Due to the complex nature of this query, without indexes, this query is incredibly slow. By indexing the affiliation 
name and publications, and the publications id, year, and numCitations fields, which are all heavily used in this query,
the query runs much faster.
- **View**: A view was created to back the Followed Universities widget. This is because a new table was created to 
track followed universities and this table only holds the university id and rating so as to not duplicate the rest of 
the university fields. So, a view is created to join the new followed table and the universities table so that the 
followed widget can still display the university name and photo url and not have to write a join every time to call this.
- **SQL Prepared Statements**: Used in the MySQL queries to retrieve professor data, professor publication details, and professor keyword trends. By using prepared statements with placeholders for parameter values, we are able to send the query to the database to be parsed and compiled once, and then execute with provided parameters. This reduces overhead since it only needs to be parsed once and then can be executed multiple times, with different values. This is useful in this case since pressing the Show More button for different professors resulted in the same exact query, just different professor id values. 

## Extra Credit Capabilities
- Data cleaning for faculty research_interests (things like inconsistent formatting, strings like "&amp" included, etc.)
- Professor top 20 keyword trends over time chart

## Contributions

**Alex (aroh2): 22 hours** 
- Professor List Widget Implementation
   - With an additional show more button, displaying extended information about a professor and their publications and trends
   - SQL Prepared statements
- Followed Professors Widget Implementation
   - With ability to change rating
   - Remove button functionality
- Related Keywords and Professors Widget implementation
   - Match multiple keywords, ranking professors based on number of matches
   - Click on professor to view related professors, and their number of shared keywords with professor of interest
- README
   - Demo
   - Installation
   - Usage
   - Design
   - Database Techniques (SQL prepared statements)
   - Extra-credit

**Ethan (edhowes2): 17 hours**
- Design and planning of dashboard layout, widget functionalities, and database interactions
   - Created google doc for planning and sketched out dashboard in Google Slides
- Citation Trends per university Widget implementation
   - Use Indexing database technique for this
   - Ability to select multiple universities via dropdown
- University List Widget implementation
   - With follow button functionality
- Followed Universities Widget implementation
   -  Use View database technique for this
   -  Rating update functionality
- README
   - Set up outline
   - Purpose section
   - Installation section
   - Design section (the three university widgets)
   - Database Techniques section (Indexing and View)
   - Implementation section

