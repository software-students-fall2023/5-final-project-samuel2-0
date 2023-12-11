
from flask import Flask,render_template
from pymongo import MongoClient

app = Flask(__name__)

def connection_db():
    """
    make a connection to db
    """
    return MongoClient("mongodb://mongo:27017/")

client = connection_db()
db = client["db"]


@app.route("/")
def welcome():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)








