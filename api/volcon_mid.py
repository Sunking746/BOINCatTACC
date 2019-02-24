#!/usr/bin/env python3


"""
BASICS

Connects and updates the list of VolCon instances and runners.
Does not receive results (volcon_results.py)
"""


import datetime
from flask import Flask, request, send_file, jsonify
import hashlib
import json
import redis


app = Flask(__name__)

r = redis.Redis(host = '0.0.0.0', port = 6389, db = 3)



# Checks a password withe respective type of Volcon system (mirrors)
def bad_password(volcon_type, given_password):

    try:
        system_key = r.hget(volcon_type, "Organization Token").decode("UTF-8")
        hp = password = hashlib.sha256(given_password.encode('UTF-8')).hexdigest()

        if hp == system_key:
            return False
        return True

    except:
        return True



# Given two lists, returns those values that are lacking in the second
# Empty if list 2 contains those elements
def l2_contains_l1(l1, l2):

    return[elem for elem in l1 if elem not in l2]



# Ensures that the server is ADTDP available
@app.route("/volcon/v2/api/available")
def volcon_server():
    return "Server is VolCon able"



# Adds a VolCon mirror
# Each VolCon mirror is saved as a hash by the name M-{IP}, it is also provided as a key pair M-{IP}:"Organization Token" inside VolCon
# This key can be used in the future if an administrator wishes to disconnect any VolCon client from the system
# Requires a json input
@app.route('/volcon/v2/api/mirrors/addme', methods=['POST'])
def addme():

    # Ensures that there is an appropriate json request
    if not request.is_json:
        return "INVALID: Request is not json"

    proposal = request.get_json()

    # Checks the required fields
    req_fields = ["key", "disconnect-key"]
    req_check = l2_contains_l1(req_fields, proposal.keys())

    if req_check != []:
        return "INVALID: Lacking the following json fields to be read: "+",".join([str(a) for a in req_check])

    if bad_password("VolCon", proposal["key"]):
        return "INVALID: incorrect password"

    IP = request.environ['REMOTE_ADDR']

    if r.hexists("VolCon", "M-"+IP):
        return "INVALID: Server IP has already been assigned"

    V = {"IP":IP,
        "disconnect-key": proposal["disconnect-key"]
    }

    r.hmset("M-"+IP, V)
    r.hset("VolCon", "M-"+IP, proposal["disconnect-key"])
    r.hincrby("VolCon", "Available-Mirrors", 1)

    return "Successfully added to the list of mirrors"




if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5089, debug=False, threaded=True)

