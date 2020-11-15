from flask import Flask
from flask_cors import CORS, cross_origin
from flask import jsonify
from flask import request
from flask_pymongo import pymongo

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
client = pymongo.MongoClient(
    "mongodb+srv://neil:different@activitylogger.sveyt.mongodb.net/logger?retryWrites=true&w=majority")


@app.route('/signup', methods=['POST'])
@cross_origin()
def create_user():
    resp = request.get_json()
    if (client.logger.users.find_one({"email": resp['email']}) == None):
        client.logger.users.insert_one(resp)
        if (resp['admin']):
            admin = client.logger.users.find_one({"email": resp['email']})
            client.logger.teams.insert_one({'admin': admin['_id'], 'users':[]})
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
    print(client.logger.teams.find_one({"users":user['_id']}))
    if (client.logger.teams.find_one({"users":user['_id']}) != None):
        return jsonify(status='error', message='User exists in a different team.')
    if (user == None):
        return jsonify(status='error', message='Email doesn\'t exist')
    client.logger.teams.update({"admin": admin['_id']}, {'$push': {'users': user['_id']}})
    return jsonify(status='INSERTED')

@app.route('/removeuser', methods=['POST'])
def remove_user_from_team():
    resp = request.get_json()
    admin = client.logger.users.find_one({"email": resp['adminEmail']})
    user = client.logger.users.find_one({"email": resp['userEmail']})
    client.logger.teams.update({"admin": admin['_id']}, {'$pull': {'users': user['_id']}})
    return jsonify(status='REMOVED')


@app.route('/login', methods=['POST'])
def user_login():
    resp = request.get_json()
    print(resp)
    user = client.logger.users.find_one({"email" : resp['email']})
    if (user != None):
        if (resp['password'] == user['password']):
            return jsonify(status = 'Login Successful', user = user)
        else:
            return jsonify(status = 'error', message = 'Username and Password don\'t match')
    else:
        return jsonify(status = 'error', message = 'User does not exist')

if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)
