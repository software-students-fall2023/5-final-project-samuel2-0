

from flask import Flask,render_template
from pymongo import MongoClient

app = Flask(__name__)

"""
def connection_db():
  
    return MongoClient("mongodb://mongo:27017/")

client = connection_db()
db = client["db"]

db.users.insert_one({"name":"lemon"})
"""

@app.route("/")
def welcome():
    return render_template("index.html")

"""
@app.route("/test")
def test():
    user = db.users.find_one({"name":"lemon"})
    return render_template("test.html", user=user)
"""


@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/inbox")
def inbox():
    return render_template("inbox.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
