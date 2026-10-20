/***********************************************************************
* File: submission.sql
* Author: Casey Tom
* Description: SQL Query for Movie Recommendation
* Course: CSE 511
***********************************************************************/

-- Query 1: Total number of movies for each genre
CREATE TABLE query1 AS
SELECT g.name, COUNT(h.movieid) AS moviecount
FROM genres AS g
JOIN hasagenre AS h 
  ON g.genreid = h.genreid
GROUP BY g.name;

-- Query 2: Average rating per genre
CREATE TABLE query2 AS
SELECT g.name, AVG(r.rating) AS rating
FROM genres AS g
JOIN hasagenre AS h 
  ON g.genreid = h.genreid
JOIN movies AS m
  ON h.movieid = m.movieid
JOIN ratings AS r 
  ON m.movieid = r.movieid
GROUP BY g.name;

-- Query 3: Movies with at least 10 ratings
CREATE TABLE query3 AS
SELECT m.title, COUNT(r.rating) AS countofratings
FROM movies AS m
JOIN ratings AS r 
  ON m.movieid = r.movieid
GROUP BY m.title
HAVING COUNT(r.rating) >= 10;

-- Query 4: All Comedy movies (movieid, title)
CREATE TABLE query4 AS
SELECT m.movieid, m.title
FROM movies AS m
JOIN hasagenre AS h 
  ON m.movieid = h.movieid
JOIN genres AS g 
  ON h.genreid = g.genreid
WHERE g.name = 'Comedy';

-- Query 5: Average rating per movie
CREATE TABLE query5 AS
SELECT m.title AS title, AVG(r.rating) AS average
FROM movies AS m
JOIN ratings AS r
  ON m.movieid = r.movieid
GROUP BY m.title;

-- Query 6: Average rating for all Comedy movies
CREATE TABLE query6 AS
SELECT AVG(r.rating) AS average
FROM ratings AS r
JOIN movies AS m
  ON r.movieid = m.movieid
JOIN hasagenre AS h
  ON m.movieid = h.movieid
JOIN genres AS g
  ON h.genreid = g.genreid
WHERE g.name = 'Comedy';

-- Query 7: Average rating for movies that are both Comedy and Romance
CREATE TABLE query7 AS
SELECT AVG(r.rating) AS average
FROM ratings AS r
JOIN (
    SELECT m.movieid
    FROM movies AS m
    JOIN hasagenre AS h
      ON m.movieid = h.movieid
    JOIN genres AS g
      ON h.genreid = g.genreid
    WHERE g.name IN ('Comedy', 'Romance')
    GROUP BY m.movieid
    HAVING COUNT(DISTINCT g.name) = 2
) AS both_genres
  ON r.movieid = both_genres.movieid;

-- Query 8: Average rating for movies that are Romance but not Comedy
CREATE TABLE query8 AS
SELECT AVG(r.rating) AS average
FROM ratings AS r
JOIN (
    SELECT m.movieid
    FROM movies AS m
    JOIN hasagenre AS h
      ON m.movieid = h.movieid
    JOIN genres AS g
      ON h.genreid = g.genreid
    GROUP BY m.movieid
    HAVING
        COUNT(CASE WHEN g.name = 'Romance' THEN 1 END) >= 1
        AND COUNT(CASE WHEN g.name = 'Comedy' THEN 1 END) = 0
) AS only_romance
  ON r.movieid = only_romance.movieid;

-- Query 9: Movies rated by a given user (v1)
CREATE TABLE query9 AS
SELECT r.movieid, r.rating
FROM ratings AS r
WHERE r.userid = :v1;



