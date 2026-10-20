/***********************************************************************
* File: submission.sql
* Author: Casey Tom
* Description: Create Movie Recommendation Database schema
* Course: CSE 511
***********************************************************************/

-- Base entity tables
-- Creating users table
CREATE TABLE users (
    userid INTEGER,
    name TEXT NOT NULL,
    PRIMARY KEY (userid)
);

-- Creating movie table
CREATE TABLE movies (
    movieid INTEGER,
    title TEXT NOT NULL,
    PRIMARY KEY (movieid)
);

-- Creating taginfo table
CREATE TABLE taginfo (
    tagid INTEGER,
    content TEXT NOT NULL,
    PRIMARY KEY (tagid)
);

-- Creating genres table
CREATE TABLE genres (
    genreid INTEGER,
    name TEXT NOT NULL,
    PRIMARY KEY (genreid)
);

-- Relational tables
-- Creating ratings table
CREATE TABLE ratings (
    userid INTEGER,
    movieid INTEGER,
    rating NUMERIC CHECK (rating >= 0 AND rating <= 5),
    timestamp BIGINT,
    PRIMARY KEY (userid, movieid),
    FOREIGN KEY (userid) REFERENCES users(userid),
    FOREIGN KEY (movieid) REFERENCES movies(movieid)
);

-- Creating tags table
CREATE TABLE tags (
    userid INTEGER,
    movieid INTEGER,
    tagid INTEGER,
    timestamp BIGINT,
    PRIMARY KEY (userid, movieid, tagid),
    FOREIGN KEY (userid) REFERENCES users(userid),
    FOREIGN KEY (movieid) REFERENCES movies(movieid),
    FOREIGN KEY (tagid) REFERENCES taginfo(tagid)
);

-- Creating hasagenre table
CREATE TABLE hasagenre (
    movieid INTEGER,
    genreid INTEGER,
    PRIMARY KEY (movieid, genreid),
    FOREIGN KEY (movieid) REFERENCES movies(movieid),
    FOREIGN KEY (genreid) REFERENCES genres(genreid)
);

