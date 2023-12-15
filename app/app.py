
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

def connection_db():
    """
    Connect to DB
    """
    return MongoClient("mongodb://localhost:27017/")

client = connection_db()
db = client["letterbox_db"]
users_collection = db['users']

def get_user(user_id):
    print(users_collection.find_one({'_id': ObjectId(user_id)}))
    return users_collection.find_one({'_id': ObjectId(user_id)})

@app.route("/")
def welcome():
    if "userid" in session:
        return render_template("index.html",name=session["username"])
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
                session["username"] = user["username"]
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
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        
        user = db.users.find_one({"name": username})
        if(user is not None):
            print("user already exists")
            return redirect(url_for("login"))
        """
        'about'
        'country'
        'age'
        'languages'
        'interests'
        """

        #if user is None, create a new account
        account = {"email": email,
                "username": username,
                "password": password,
                "first_name":first_name,
                "last_name":last_name,
                "name" : first_name + " " + last_name,
                "about_me": "I am testing about1",
                "age" : 22,
                "languages" : "English",
                "interests" : "Food",
                "country" : "USA"
                }
        print("account", account)
        
        db.users.insert_one(account)
        
        new_user = db.users.find_one({"username":username})
        print("hello")
        print("nw user", new_user)
        if new_user is not None:
            session["userid"] = str(new_user["_id"])
            session["email"] = new_user["email"]
            session["username"] = new_user["username"]
            print(session)
    else:
        return render_template("signup.html")
    
    return redirect(url_for("welcome"))


@app.route("/logout")
def logout():
    if "userid" in session :
        session.pop("userid", None)
        session.pop("email", None)
        session.pop("username", None)

    return redirect(url_for("welcome"))


@app.route("/inbox")
def inbox():
    return render_template("inbox.html")


@app.route("/profile/<user_id>", methods=["GET"])
def myprofile(user_id):
    user = get_user(user_id)
    if user:
        return render_template("profile.html", user=user)
    else:
         return render_template("404.html", message='User not found. Log in first.'), 404


@app.route("/profile/<user_id>/edit_profile", methods=["GET"])
def edit_profile(user_id):
    user = get_user(user_id)
    if user:
        return render_template("edit_profile.html", user=user)
    else:
       return 'User not found. Log in first.', 404


@app.route("/profile/<user_id>/edit_profile", methods=["POST"])
def update_profile(user_id):
    user = get_user(user_id)
    if user:
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']
        country = request.form['country']
        myquery = {"_id": ObjectId(user.get("_id"))}
        doc = {"$set":{"username":username,
                       "first_name":first_name,
                       "last_name":last_name,
                       "name": first_name + " " + last_name,
                       "age":age,
                       "country": country
                       }}
        users_collection.update_one(myquery,doc)
        user['username'] = username
        user['first_name'] = first_name
        user['last_name'] = last_name
        user['name'] = first_name + " " + last_name
        user['age'] = age
        user['country'] = country
        return render_template("profile.html", user=user)
    else:
       return 'User not found. Log in first.', 404

@app.route("/profile/<user_id>/edit_interests", methods=["GET"])
def edit_interests(user_id):
    user = get_user(user_id)
    if user:
        return render_template("edit_interests.html", user=user)
    else:
       return 'User not found. Log in first.', 404

@app.route("/profile/<user_id>/edit_interests", methods=["POST"])
def update_interests(user_id):
    user = get_user(user_id)
    if user:
        new_interests = request.form.getlist('interests[]')  
        user['interests'] = new_interests
        users_collection.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"interests": new_interests}})

        return render_template("profile.html", user=user)
    else:
       return 'User not found. Log in first.', 404

@app.route("/profile/<user_id>/edit_languages")
def edit_languages(user_id):
    user = get_user(user_id)
    if user:
        return render_template("edit_languages.html", user=user)
    else:
       return 'User not found. Log in first.', 404

@app.route("/profile/<user_id>/edit_languages", methods=["POST"])
def update_languages(user_id):
    user = get_user(user_id)
    if user:
        new_languages = request.form.getlist('languages[]')  
        user['languages'] = new_languages
        users_collection.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"languages": new_languages}})
        return render_template("profile.html", user=user)
    else:
       return 'User not found. Log in first.', 404
    
@app.route("/profile/<user_id>/edit_about", methods=["GET"])
def edit_about(user_id):
    user = get_user(user_id)
    if user:
        return render_template("edit_about.html", user=user)
    else:
       return 'User not found. Log in first.', 404

@app.route("/profile/<user_id>/edit_about", methods=["POST"])
def update_about(user_id):
    user = get_user(user_id)
    if user:
        user['about_me'] = request.form['about']
        users_collection.update_one({"_id": user["_id"]}, {"$set": {"about_me": request.form["about"]}})
        return render_template("profile.html", user=user)
    else:
       return 'User not found. Log in first.', 404
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)






