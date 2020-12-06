from flask import Flask
from flask_cors import CORS, cross_origin
from flask import jsonify
from flask import request
from flask import send_file
from flask_pymongo import pymongo
from bson import ObjectId
import re
import os

app = Flask(__name__)
cors = CORS(app)
client = pymongo.MongoClient(
    "mongodb+srv://neil:different@activitylogger.sveyt.mongodb.net/logger?retryWrites=true&w=majority")


@app.route('/signup', methods=['POST'])
def create_user():
    resp = request.get_json()
    if (client.logger.users.find_one({"email": resp['email']}) == None):
        client.logger.users.insert_one(resp)
        if (resp['admin']):
            admin = client.logger.users.find_one({"email": resp['email']})
            client.logger.teams.insert_one(
                {'admin': admin['_id'], 'users': [admin['_id']]})
        return jsonify(status='INSERTED')
    else:
        return jsonify(status='error', message='Account with that email exists')


@app.route('/adduser', methods=['POST'])
def add_user_to_team():
    resp = request.get_json()
    admin = client.logger.users.find_one({"email": resp['adminEmail']})
    user = client.logger.users.find_one({"email": resp['userEmail']})
    team = client.logger.teams.find_one({"admin": admin['_id']})
    if (user['_id'] in team['users']):
        return jsonify(status='error', message='User already exists in this team.')
    print(client.logger.teams.find_one({"users": user['_id']}))
    if (client.logger.teams.find_one({"users": user['_id']}) != None):
        return jsonify(status='error', message='User exists in a different team.')
    if (user == None):
        return jsonify(status='error', message='Email doesn\'t exist')
    client.logger.teams.update({"admin": admin['_id']}, {
                               '$push': {'users': user['_id']}})
    return jsonify(status='INSERTED')


@app.route('/removeuser', methods=['POST'])
def remove_user_from_team():
    resp = request.get_json()
    admin = client.logger.users.find_one({"email": resp['adminEmail']})
    user = client.logger.users.find_one({"email": resp['userEmail']})
    client.logger.teams.update({"admin": admin['_id']}, {
                               '$pull': {'users': user['_id']}})
    return jsonify(status='REMOVED')


@app.route('/findteam', methods=['POST'])
def find_team():
    resp = request.get_json()
    user = client.logger.users.find_one({"email": resp['userEmail']})
    team = client.logger.teams.find_one({"users": user['_id']})
    users = []
    for i in team['users']:
        users.append(client.logger.users.find_one({"_id": i}, {'_id': 0}))
    if (team == None):
        return jsonify(status='error', message='User not on a team.')
    return jsonify(status='TEAM FOUND', team=users)


@app.route('/search', methods=['POST'])
def search_email():
    resp = request.get_json()
    matched = client.logger.users.find(
        {"email": {'$regex': resp['userEmail'], '$options': '$i'}}, {'_id': 0})
    x = []
    for i in matched:
        x.append(i)
    if(len(x) != 0):
        return jsonify(status='USER FOUND', users=x)
    else:
        return jsonify(status='error', message='User does not exist.')


@app.route('/login', methods=['POST'])
def user_login():
    resp = request.get_json()
    print(resp)
    user = client.logger.users.find_one({"email": resp['email']})
    if (user != None):
        if (resp['password'] == user['password']):
            print(user)
            return jsonify(status='Login Successful', user={
                "email": user["email"],
                "isAdmin": user["admin"]
            })
        else:
            return jsonify(status='error', message='Username and Password don\'t match')
    else:
        return jsonify(status='error', message='User does not exist')

@app.route('/getLogs', methods=['POST'])
@cross_origin()
def get_all_logs():
    resp = request.get_json()
    logs = client.logger.logs.find({'application': resp['name']}, limit = 10).sort("timestamp", 1).skip(int(resp['pageNumber'])*10)
    logsView = []
    for x in logs:
        x['_id'] = str(x['_id'])
        logsView.append(x)
    return jsonify(status='SUCCESSFUL', logs = logsView)

@app.route('/getLogsByText', methods=['POST'])
@cross_origin()
def get_logs_by_text():
    resp = request.get_json()
    logs = client.logger.logs.find({"log" : {'$regex': resp['text'], '$options': '$i'}, 'application': resp['name']}, limit = 10).sort("timestamp", 1).skip(int(resp['pageNumber'])*10)
    logsView = []
    for x in logs:
        x['_id'] = str(x['_id'])
        logsView.append(x)
    return jsonify(status='SUCCESSFUL', logs = logsView)

@app.route('/getLogsByRegex', methods=['POST'])
@cross_origin()
def get_logs_by_regex():
    #{"log" : {'$regex': resp['text'], '$options': '$i'}},{'_id':0},
    resp = request.get_json()
    logs = client.logger.logs.find({"log" : {'$regex': re.compile(resp['text'])}, 'application': resp['name']}, limit = 10).sort("timestamp", 1).skip(int(resp['pageNumber'])*10)
    logsView = []
    for x in logs:
        x['_id'] = str(x['_id'])
        logsView.append(x)
    return jsonify(status='SUCCESSFUL', logs = logsView)

@app.route('/pinLogs', methods=['POST'])
@cross_origin()
def pinLogs():
    resp = request.get_json()
    user = client.logger.users.find_one({"email": resp['userEmail']})
    team = client.logger.teams.find_one({"users": user['_id']})
    client.logger.teams.update({'_id' : team['_id'], 'pinnedLogs': {'$exists' : False}}, {'$set' : {'pinnedLogs' : {'frontend-website' : [], 'java-backend': [], 'mongo-db': []}}})
    log = client.logger.logs.find_one({'_id': ObjectId(resp['logID'])})
    client.logger.teams.update({"_id": team['_id']}, {'$push': {'pinnedLogs.{}'.format(log['application']): ObjectId(log['_id'])}})
    return jsonify(status='SUCCESSFUL')

@app.route('/removePinLogs', methods=['POST'])
@cross_origin()
def removePinLogs():
    resp = request.get_json()
    user = client.logger.users.find_one({"email": resp['userEmail']})
    team = client.logger.teams.find_one({"users": user['_id']})
    log = client.logger.logs.find_one({'_id': ObjectId(resp['logID'])})
    client.logger.teams.update({"_id": team['_id']}, {'$pull': {'pinnedLogs.{}'.format(log['application']): ObjectId(log['_id'])}})
    return jsonify(status='SUCCESSFUL')

@app.route('/getPinnedLogs', methods=['POST'])
@cross_origin()
def get_pinned_logs():
    resp = request.get_json()
    user = client.logger.users.find_one({"email": resp['userEmail']})
    team = client.logger.teams.find_one({"users": user['_id']})
    logs = client.logger.logs.find({"_id": {"$in": team["pinnedLogs"][resp["application"]]}})
    logsView = []
    for x in logs:
        x['_id'] = str(x['_id'])
        logsView.append(x)
    return jsonify(status='SUCCESSFUL', logs=logsView)


@app.route('/exportLogs', methods=['POST'])
@cross_origin()
def export_logs():
    resp = request.get_json()
    logs = client.logger.logs.find({"log": {'$regex': re.compile(resp['text'])}, 'application': resp['name']}).sort("timestamp", 1)
    file = open("logs.csv", 'w')
    for log in logs:
        file.write(str(log["timestamp"]) + "," + log["level"] + "," + log["log"] + "\n")
    file.close()

    return send_file("logs.csv", as_attachment=True)



if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)