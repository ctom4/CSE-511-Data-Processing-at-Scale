#!/usr/bin/python3
#
# Interface for the assignment
#

import psycopg2

def getOpenConnection(user='postgres', password='1234', dbname='postgres'):
    return psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='localhost' password='" + password + "'")

# ==========================================================
#                     LOAD RATINGS
# ==========================================================
def loadRatings(ratingstablename, ratingsfilepath, openconnection):
    cursor = openconnection.cursor()

    cursor.execute(f"DROP TABLE IF EXISTS {ratingstablename}")

    cursor.execute(
        f"""
        CREATE TABLE {ratingstablename} (
            userid INT,
            movieid INT,
            rating FLOAT
        )
        """
    )

    with open(ratingsfilepath, 'r') as file:
        for line in file:
            parts = line.strip().split("::")
            if len(parts) < 3:
                continue
            userid = int(parts[0])
            movieid = int(parts[1])
            rating = float(parts[2])
            cursor.execute(
                f"INSERT INTO {ratingstablename} (userid, movieid, rating) VALUES (%s, %s, %s)",
                (userid, movieid, rating)
            )

    openconnection.commit()
    cursor.close()

# ==========================================================
#                     RANGE PARTITION
# ==========================================================
def rangePartition(ratingstablename, numberofpartitions, openconnection):
    cursor = openconnection.cursor()

    interval = 5.0 / numberofpartitions

    # Create range partitions
    for i in range(numberofpartitions):
        part_name = f"range_part{i}"
        cursor.execute(f"DROP TABLE IF EXISTS {part_name}")
        cursor.execute(
            f"""
            CREATE TABLE {part_name} (
                userid INT,
                movieid INT,
                rating FLOAT
            )
            """
        )

    # Fill partitions
    for i in range(numberofpartitions):
        part_name = f"range_part{i}"
        minr = i * interval
        maxr = (i + 1) * interval

        if i == 0:
            cursor.execute(
                f"""
                INSERT INTO {part_name}
                SELECT * FROM {ratingstablename}
                WHERE rating >= {minr} AND rating <= {maxr}
                """
            )
        else:
            cursor.execute(
                f"""
                INSERT INTO {part_name}
                SELECT * FROM {ratingstablename}
                WHERE rating > {minr} AND rating <= {maxr}
                """
            )

    # Create metadata table (REQUIRED BY AUTOGRADER)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            method TEXT,
            numberofpartitions INT
        )
        """
    )

    cursor.execute("DELETE FROM metadata WHERE method = 'range'")
    cursor.execute(
        "INSERT INTO metadata (method, numberofpartitions) VALUES ('range', %s)",
        (numberofpartitions,)
    )

    # Range metadata table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rangeratingsmetadata (
            partitionnum INT,
            minrating REAL,
            maxrating REAL
        )
        """
    )

    cursor.execute("DELETE FROM rangeratingsmetadata")

    for i in range(numberofpartitions):
        minr = i * interval
        maxr = (i + 1) * interval
        cursor.execute(
            "INSERT INTO rangeratingsmetadata(partitionnum, minrating, maxrating) VALUES (%s, %s, %s)",
            (i, minr, maxr)
        )

    openconnection.commit()
    cursor.close()

# ==========================================================
#                 ROUND ROBIN PARTITION
# ==========================================================
def roundRobinPartition(ratingstablename, numberofpartitions, openconnection):
    cursor = openconnection.cursor()

    # Create partitions
    for i in range(numberofpartitions):
        part_name = f"rrobin_part{i}"
        cursor.execute(f"DROP TABLE IF EXISTS {part_name}")
        cursor.execute(
            f"""
            CREATE TABLE {part_name} (
                userid INT,
                movieid INT,
                rating FLOAT
            )
            """
        )

    cursor.execute(f"SELECT userid, movieid, rating FROM {ratingstablename}")
    rows = cursor.fetchall()

    # Distribute rows in RR
    for index, row in enumerate(rows):
        partition_index = index % numberofpartitions
        part_name = f"rrobin_part{partition_index}"
        cursor.execute(
            f"INSERT INTO {part_name} (userid, movieid, rating) VALUES (%s, %s, %s)",
            row
        )

    # Metadata table (REQUIRED)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            method TEXT,
            numberofpartitions INT
        )
        """
    )

    cursor.execute("DELETE FROM metadata WHERE method = 'roundrobin'")
    cursor.execute(
        "INSERT INTO metadata (method, numberofpartitions) VALUES ('roundrobin', %s)",
        (numberofpartitions,)
    )

    # RR table (used by Query Processing)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS roundrobinratingsmetadata(
            partitionnum INT
        )
        """
    )

    cursor.execute("DELETE FROM roundrobinratingsmetadata")

    for i in range(numberofpartitions):
        cursor.execute(
            "INSERT INTO roundrobinratingsmetadata(partitionnum) VALUES (%s)",
            (i,)
        )

    openconnection.commit()
    cursor.close()

# ==========================================================
#                 ROUND ROBIN INSERT
# ==========================================================
def roundrobininsert(ratingstablename, userid, itemid, rating, openconnection):
    cursor = openconnection.cursor()

    cursor.execute(
        f"INSERT INTO {ratingstablename} (userid, movieid, rating) VALUES (%s, %s, %s)",
        (userid, itemid, rating)
    )

    cursor.execute("SELECT numberofpartitions FROM metadata WHERE method = 'roundrobin'")
    result = cursor.fetchone()

    if result:
        n = result[0]

        cursor.execute(f"SELECT COUNT(*) FROM {ratingstablename}")
        row_count = cursor.fetchone()[0]

        partition_index = (row_count - 1) % n
        part_name = f"rrobin_part{partition_index}"

        cursor.execute(
            f"INSERT INTO {part_name} (userid, movieid, rating) VALUES (%s, %s, %s)",
            (userid, itemid, rating)
        )

    openconnection.commit()
    cursor.close()

# ==========================================================
#                 RANGE INSERT
# ==========================================================
def rangeinsert(ratingstablename, userid, itemid, rating, openconnection):
    cursor = openconnection.cursor()

    cursor.execute(
        f"INSERT INTO {ratingstablename} (userid, movieid, rating) VALUES (%s, %s, %s)",
        (userid, itemid, rating)
    )

    cursor.execute("SELECT numberofpartitions FROM metadata WHERE method = 'range'")
    result = cursor.fetchone()

    if result:
        n = result[0]
        interval = 5.0 / n

        for i in range(n):
            lower = i * interval
            upper = (i + 1) * interval
            if (i == 0 and lower <= rating <= upper) or (i > 0 and lower < rating <= upper):
                part_name = f"range_part{i}"
                cursor.execute(
                    f"INSERT INTO {part_name} (userid, movieid, rating) VALUES (%s, %s, %s)",
                    (userid, itemid, rating)
                )
                break

    openconnection.commit()
    cursor.close()

# ==========================================================
#                CLEANUP HELPERS
# ==========================================================
def deletepartitions(openconnection):
    cursor = openconnection.cursor()

    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
          AND (table_name LIKE 'range_part%%' OR table_name LIKE 'rrobin_part%%')
    """)

    for (t,) in cursor.fetchall():
        cursor.execute(f"DROP TABLE IF EXISTS {t} CASCADE")

    cursor.execute("DELETE FROM metadata WHERE method IN ('range','roundrobin')")

    openconnection.commit()
    cursor.close()

def createDB(dbname='dds_assignment'):
    con = getOpenConnection(dbname='postgres')
    con.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()

    cur.execute(f"SELECT COUNT(*) FROM pg_database WHERE datname='{dbname}'")
    if cur.fetchone()[0] == 0:
        cur.execute(f"CREATE DATABASE {dbname}")
    else:
        print(f'A database named "{dbname}" already exists')

    cur.close()
    con.close()

def deletepartitionsandexit(openconnection):
    cursor = openconnection.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    for (t,) in cursor.fetchall():
        cursor.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    cursor.close()

def deleteTables(ratingstablename, openconnection):
    try:
        cursor = openconnection.cursor()
        if ratingstablename.upper() == 'ALL':
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            for (t,) in cursor.fetchall():
                cursor.execute(f"DROP TABLE {t} CASCADE")
        else:
            cursor.execute(f"DROP TABLE {ratingstablename} CASCADE")

        openconnection.commit()
    finally:
        cursor.close()
