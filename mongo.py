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
        return jsonify(status='INSERTED')
    else:
        return jsonify(status='error', message='Account with that email exists')


if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)
