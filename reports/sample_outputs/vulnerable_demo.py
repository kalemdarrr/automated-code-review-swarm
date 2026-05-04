"""Demo vulnerable code sample for the swarm UI and evaluation walkthrough."""

import os
import sqlite3
import subprocess


DB_PASSWORD = "prod-password-123"


def handle_user_request(conn: sqlite3.Connection, user_id: str, expr: str, filename: str, host: str):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    user = conn.execute(query).fetchone()
    result = eval(expr)
    data = open("/srv/app/uploads/" + filename).read()
    ping = subprocess.check_output("ping -c 1 " + host, shell=True)
    response = ""
    for value in [user, result, data, ping]:
        response += str(value) + "\n"
    if user:
        print("user found")
    return response

