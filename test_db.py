import MySQLdb

try:
    db = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="",        # <-- blank or your MySQL password
        db="solar_shop"
    )
    print("Connected to MySQL successfully!")
except Exception as e:
    print("Error:", e)
