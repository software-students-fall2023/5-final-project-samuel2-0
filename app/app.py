
import os
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    session
    )
from pymongo import MongoClient
from bson.objectid import ObjectId


app = Flask(__name__)
app.secret_key = os.urandom(24)


#"mongodb://mongo:27017/"
def connection_db():
    """
    Connect to DB
    """
    return MongoClient("mongodb://localhost:27017/")

client = connection_db()
db = client["letterbox_db"]

@app.route("/", methods=["GET"])
def welcome():
    if "userid" in session:
        return render_template("index.html",name=session["name"])
    return render_template("index.html")


@app.route("/login", methods=["GET","POST"])
def login():
    """
    Login method for users
    """
    incorrect_pass = False
    incorrect_email = False

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.users.find_one({
            "email":email
        })
        
        if user is None:
            print("USER NOT FOUND")
            incorrect_email = True

        if user is not None:
            if password != user["password"]:
                incorrect_pass = True
                print("INCORRECT PASSWORD")
                
            else:
                session["userid"] = str(user["_id"])
                session["email"] = user["email"]
                session["name"] = user["name"]
                return redirect(url_for("welcome"))
            
        return render_template("login.html",incorrect_pass=incorrect_pass,incorrect_email=incorrect_email)
    
    if request.method == "GET":
        return render_template("login.html")
    

    return redirect(url_for("signup"))

    
@app.route("/signup", methods=["POST", "GET"])
def signup():
    """
    Sign up method for new users
    """
    
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
        
        new_user = db.users.find_one({"name":username})
        if new_user is not None:
            #print(type(str(new_user["_id"])))
            session["userid"] = str(new_user["_id"])
            session["email"] = new_user["email"]
            session["name"] = new_user["name"]
            print(session)
        
        
    else:
        return render_template("signup.html")
    
    return redirect(url_for("welcome"))


@app.route("/logout")
def logout():
    if "userid" in session :
        session.pop("userid", None)
        session.pop("email", None)
        session.pop("name", None)

    return redirect(url_for("welcome"))


@app.route("/inbox")
def inbox():
    return render_template("inbox.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
