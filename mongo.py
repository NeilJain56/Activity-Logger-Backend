from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import pymongo

app = Flask(__name__)
client = pymongo.MongoClient(
    "mongodb+srv://neil:different@activitylogger.sveyt.mongodb.net/logger?retryWrites=true&w=majority")


@app.route('/signup', methods=['POST'])
def create_user():
    client.logger.users.insert_one(request.get_json())
    return "INSERTED"


if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)
