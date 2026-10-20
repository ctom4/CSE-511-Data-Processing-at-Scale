#!/usr/bin/python3
#
# Interface for Query Processing Assignment
#

import psycopg2
import os
import sys

DATABASE_NAME = 'dds_assignment'
RATINGS_TABLE_NAME = 'ratings'
RANGE_TABLE_PREFIX = 'range_part'
RROBIN_TABLE_PREFIX = 'rrobin_part'
RANGE_QUERY_OUTPUT_FILE = 'RangeQueryOut.txt'
POINT_QUERY_OUTPUT_FILE = 'PointQueryOut.txt'
RANGE_RATINGS_METADATA_TABLE = 'rangeratingsmetadata'
RROBIN_RATINGS_METADATA_TABLE = 'roundrobinratingsmetadata'

# Do not close the connection inside this file i.e. do not perform openconnection.close()
def RangeQuery(ratingsTableName, ratingMinValue, ratingMaxValue, openconnection):
    """
    Queries range and round-robin partitions for ratings within a specified range.
    Writes results to RangeQueryOut.txt
    :return: None
    """
    cursor = openconnection.cursor()  # Changed from 'cur' to 'cursor'
    rows = []

    # Query relevant range partitions using metadata
    cursor.execute(
        f"""
        SELECT partitionnum, minrating, maxrating
        FROM {RANGE_RATINGS_METADATA_TABLE}
        WHERE maxrating >= %s AND minrating <= %s
        ORDER BY partitionnum
        """,
        (ratingMinValue, ratingMaxValue)
    )
    range_parts = cursor.fetchall()

    # Get data from relevant range partitions
    for partnum, minr, maxr in range_parts:
        partition_table = f"{RANGE_TABLE_PREFIX}{partnum}"  # More descriptive
        try:
            cursor.execute(
                f"""SELECT userid, movieid, rating
                    FROM {partition_table}
                    WHERE rating >= %s AND rating <= %s""",
                (ratingMinValue, ratingMaxValue)
            )
            for userid, movieid, rating in cursor.fetchall():
                rows.append((partition_table, userid, movieid, rating))
        except:
            continue  # Skip partition if it doesn't exist

    # Query all round-robin partitions
    cursor.execute(f"SELECT MAX(partitionnum) FROM {RROBIN_RATINGS_METADATA_TABLE}")
    max_partition = cursor.fetchone()[0]

    if max_partition is not None:
        total_partitions = max_partition + 1
        for i in range(total_partitions):
            rrobin_table = f"{RROBIN_TABLE_PREFIX}{i}"
            try:
                cursor.execute(
                    f"""SELECT userid, movieid, rating
                        FROM {rrobin_table}
                        WHERE rating >= %s AND rating <= %s""",
                    (ratingMinValue, ratingMaxValue)
                )
                for userid, movieid, rating in cursor.fetchall():
                    rows.append((rrobin_table, userid, movieid, rating))
            except:
                continue  # Skip partition if it doesn't exist

    # Sort results for consistent output
    rows.sort(key=lambda x: (x[0], int(x[1]), int(x[2]), float(x[3])))

    # Write results to file
    writeToFile(RANGE_QUERY_OUTPUT_FILE, rows)
    cursor.close()


def PointQuery(ratingsTableName, ratingValue, openconnection):
    """
    Queries range and round-robin partitions for an exact rating value.
    Writes results to PointQueryOut.txt
    :return: None
    """
    cursor = openconnection.cursor()
    rows = []

    # Query specific range partition using metadata
    cursor.execute(
        f"""
        SELECT partitionnum, minrating, maxrating
        FROM {RANGE_RATINGS_METADATA_TABLE}
        WHERE %s >= minrating AND %s <= maxrating
        ORDER BY partitionnum
        """,
        (ratingValue, ratingValue)
    )
    range_parts = cursor.fetchall()

    # Get data from the specific range partition
    for partnum, minr, maxr in range_parts:
        partition_table = f"{RANGE_TABLE_PREFIX}{partnum}"
        try:
            cursor.execute(
                f"SELECT userid, movieid, rating FROM {partition_table} WHERE rating = %s",
                (ratingValue,)
            )
            for userid, movieid, rating in cursor.fetchall():
                rows.append((partition_table, userid, movieid, rating))
        except:
            continue  # Skip partition if it doesn't exist

    # Query all round-robin partitions
    cursor.execute(f"SELECT MAX(partitionnum) FROM {RROBIN_RATINGS_METADATA_TABLE}")
    max_partition = cursor.fetchone()[0]

    if max_partition is not None:
        total_partitions = max_partition + 1
        for i in range(total_partitions):
            rrobin_table = f"{RROBIN_TABLE_PREFIX}{i}"
            try:
                cursor.execute(
                    f"SELECT userid, movieid, rating FROM {rrobin_table} WHERE rating = %s",
                    (ratingValue,)
                )
                for userid, movieid, rating in cursor.fetchall():
                    rows.append((rrobin_table, userid, movieid, rating))
            except:
                continue  # Skip partition if it doesn't exist

    # Sort results for consistent output
    rows.sort(key=lambda x: (x[0], int(x[1]), int(x[2]), float(x[3])))

    # Write results to file
    writeToFile(POINT_QUERY_OUTPUT_FILE, rows)
    cursor.close()


def writeToFile(filename, rows):
    f = open(filename, 'w')
    for line in rows:
        f.write(','.join(str(s) for s in line))
        f.write('\n')
    f.close()