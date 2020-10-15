from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import pymongo

app = Flask(__name__)
client = pymongo.MongoClient(
    "mongodb+srv://neil:different@activitylogger.sveyt.mongodb.net/logger?retryWrites=true&w=majority")


@app.route('/signup', methods=['POST'])
def create_user():
    resp = request.get_json()
    print(resp)
    print(client.logger.users.find_one({"email" : resp['email']}))
    if (client.logger.users.find_one({"email" : resp['email']}) == None):
        client.logger.users.insert_one(resp)
        return jsonify(status = 'INSERTED')
    else:
        return jsonify(status = 'error', message = 'Account with that email exists')


if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)
