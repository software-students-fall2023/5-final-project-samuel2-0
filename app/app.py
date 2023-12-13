

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request
    )
from pymongo import MongoClient
import bson


app = Flask(__name__)


#"mongodb://mongo:27017/"
def connection_db():
    """
    Connect to DB
    """
    return MongoClient("mongodb://localhost:27017/")

client = connection_db()
db = client["letterbox_db"]

#db.users.insert_one({"name":"lemon"})


@app.route("/", methods=["GET"])
def welcome():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")



@app.route("/signup", methods=["POST", "GET"])
def signup():
    
    if request.method == 'POST':

        username = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        #check if user already exists, if so redirect to log in
        user = db.users.find_one({"name": username})
        if(user is not None):
            print("user already exists")
            return redirect(url_for("login"))

        #if user is None, create a new account
        account = {"email": email,
                "name": username,
                "password": password,
                }
        
        db.users.insert_one(account)
        
        
    else:
        return render_template("signup.html")
    


    return redirect(url_for("welcome"))

@app.route("/inbox")
def inbox():
    return render_template("inbox.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
