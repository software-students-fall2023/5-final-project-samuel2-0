import os
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
          
def connection_db():
    """
    Connect to DB
    """
    return MongoClient("mongodb://localhost:27017/")


client = connection_db()
db = client["letterbox_db"]
users_collection = db["users"]
letters_collection = db["letters"]


def get_user(user_id):
    print(users_collection.find_one({"_id": ObjectId(user_id)}))
    return users_collection.find_one({"_id": ObjectId(user_id)})


def get_all_users():
    return users_collection.find()


@app.route("/")
def welcome():
    """
    landing page : if user is logged in, display a welcome page
    """
    if "userid" in session:
        return render_template("index.html", name=session["username"])
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login method for users
    """
    incorrect_pass = False
    incorrect_email = False

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.users.find_one({"email": email})

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
                return redirect(url_for("inbox"))

        return render_template(
            "login.html", incorrect_pass=incorrect_pass, incorrect_email=incorrect_email
        )
    if request.method == "GET":
        return render_template("login.html")
    return redirect(url_for("signup"))


@app.route("/signup", methods=["POST", "GET"])
def signup():
    """
    Sign up method for new users
    """
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]

        user = db.users.find_one({"name": username})
        if user is not None:
            print("user already exists")
            return redirect(url_for("login"))

        # if user is None, create a new account
        account = {
            "email": email,
            "username": username,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "name": first_name + " " + last_name,
            "languages": [],
            "interests": [],
        }
        print("account", account)

        db.users.insert_one(account)

        new_user = db.users.find_one({"username": username})
        print("hello")
        print("nw user", new_user)
        if new_user is not None:
            session["userid"] = str(new_user["_id"])
            session["email"] = new_user["email"]
            session["username"] = new_user["username"]
            print(session)
    else:
        return render_template("signup.html")
    return redirect(url_for("personal_info"))


@app.route("/logout")
def logout():
    """
    Allows a user to log out of current account
    """
    if "userid" in session:
        session.pop("userid", None)
        session.pop("email", None)
        session.pop("username", None)

    return redirect(url_for("welcome"))


@app.route("/inbox", methods=["GET"])
def inbox():
    """
    If a user is logged in, then the user can see letters received from others
    """
    if "userid" in session:
        userid = session["userid"]
        user = users_collection.find_one({"_id": ObjectId(userid)})
        print(user)

        if user:
            print("is user printintg", (userid))
            # find all the letters whose receipients == current logged in user
            letters = letters_collection.find({"receiver_id": ObjectId(userid)}).sort(
                "timestamp", -1
            )

            return render_template("inbox.html", user=user, letters=letters)
    return redirect(url_for("login"))


@app.route("/inbox/<letter_id>", methods=["POST"])
def remove_letter(letter_id):
    """
    A logged in user can delete a letter received from others.
    """
    if "userid" in session:
        userid = session["userid"]
        user = users_collection.find_one({"_id": ObjectId(userid)})
        print(user)

        if user:
            letterToDelete = letters_collection.find_one({"_id": ObjectId(letter_id)})
            letterToDeleteId = letterToDelete["_id"]
            letters_collection.delete_one({"_id": letterToDeleteId})
            return redirect(url_for("inbox"))

    return redirect(url_for("welcome"))


@app.route("/read_letter/<letter_id>", methods=["GET"])
def read_letter(letter_id):
    """
    A logged in user can click on a corresponding letter and read 
    """
    if "userid" in session:
        userid = session["userid"]
        user = users_collection.find_one({"_id": ObjectId(userid)})
        print(letter_id, "is None ??")
        letter = letters_collection.find_one({"_id": ObjectId(letter_id)})
       
        if user and letter:
            print("user and letter both exist")
            print("in read letter function : ", user, letter)
            return render_template("reading.html", user=user, letter=letter)
    return redirect(url_for("login"))


@app.route("/fakeALetter")
def fake_letter():
    sender_id = "657be1c210f97adccd73219b"
    receiver_id = "657cfca3d111878b03b0e4da"
    sender_name = users_collection.find_one({"_id": ObjectId(sender_id)})["username"]

    new_letter = {
        "sender_id": ObjectId(sender_id),
        "sender_name": sender_name,
        "receiver_id": ObjectId(receiver_id),
        "header": "Holy Holy",
        "letter_text": "Hi God bless!Holy Holy Holy,Holy Holy Holy,Holy Holy Holy\n,Holy Holy Holy,Holy Holy Holy</p>",
        "timestamp": datetime.now(),
    }
    letters_collection.insert_one(new_letter)
    print("successfully faked a letter")
    return redirect(url_for("login"))


@app.route("/personal_info", methods=["GET", "POST"])
def personal_info():
    """
    A logged in user can add personalized information about themselves
    """
    if "userid" in session:
        userid = session["userid"]
        user = users_collection.find_one({"_id": ObjectId(userid)})
        print("user", user)
        if user:
            if request.method == "GET":
                return render_template("personal_info.html", user=user)
            elif request.method == "POST":
                country = request.form["country"]
                about_me = request.form["about_me"]
                age = request.form["age"]
                languages = request.form.getlist("languages")
                interests = request.form.getlist("interests")
                users_collection.update_one(
                    {"_id": ObjectId(user.get("_id"))},
                    {
                        "$set": {
                            "languages": languages,
                            "interests": interests,
                            "age": age,
                            "about_me": about_me,
                            "country": country,
                        }
                    },
                )
                print(country, about_me, age, languages, interests)
                return redirect(url_for("myprofile", user_id=user.get("_id")))

    return redirect(url_for("welcome"))


@app.route("/profile", methods=["GET"])
def myprofile():
    """
    personal profile information for the logged in user 
    """
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        if user:
            return render_template("profile.html", user=user)
        else:
            return (
                render_template("404.html", message="User not found. Log in first."),
                404,
            )
    return redirect(url_for("login"))

@app.route("/profile/edit_profile", methods=["GET"])
def edit_profile():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        if user:
            return render_template("edit_profile.html", user=user)
        else:
            return (
                render_template("404.html", message="User not found. Log in first."),
                404,
            )
    return redirect(url_for("login"))


@app.route("/profile/edit_profile", methods=["POST"])
def update_profile():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        if user:
            username = request.form["username"]
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            age = request.form["age"]
            country = request.form["country"]
            myquery = {"_id": ObjectId(user.get("_id"))}
            doc = {
                "$set": {
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "name": first_name + " " + last_name,
                    "age": age,
                    "country": country,
                }
            }
            users_collection.update_one(myquery, doc)
            user["username"] = username
            user["first_name"] = first_name
            user["last_name"] = last_name
            user["name"] = first_name + " " + last_name
            user["age"] = age
            user["country"] = country
            return render_template("profile.html", user=user)
    else:
        return "User not found. Log in first.", 404


@app.route("/profile/edit_interests", methods=["GET"])
def edit_interests():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        if user:
            return render_template("edit_interests.html", user=user)
        else:
            return (
                render_template("404.html", message="User not found. Log in first."),
                404,
            )


@app.route("/profile/edit_interests", methods=["POST"])
def update_interests():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        if user:
            new_interests = request.form.getlist("interests[]")
            user["interests"] = new_interests
            users_collection.update_one(
                {"_id": ObjectId(user["_id"])}, {"$set": {"interests": new_interests}}
            )
        return render_template("profile.html", user=user)
    else:
        return render_template("404.html", message="User not found. Log in first."), 404


@app.route("/profile/edit_languages")
def edit_languages():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        if user:
            return render_template("edit_languages.html", user=user)
    else:
        return render_template("404.html", message="User not found. Log in first."), 404


@app.route("/profile/edit_languages", methods=["POST"])
def update_languages():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        if user:
            new_languages = request.form.getlist("languages[]")
            user["languages"] = new_languages
            users_collection.update_one(
                {"_id": ObjectId(user["_id"])}, {"$set": {"languages": new_languages}}
            )
            return render_template("profile.html", user=user)
    else:
        return render_template("404.html", message="User not found. Log in first."), 404


@app.route("/profile/edit_about", methods=["GET"])
def edit_about():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        if user:
            return render_template("edit_about.html", user=user)
    else:
        return render_template("404.html", message="User not found. Log in first."), 404


@app.route("/profile/edit_about", methods=["POST"])
def update_about():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        if user:
            user["about_me"] = request.form["about"]
            users_collection.update_one(
                {"_id": user["_id"]}, {"$set": {"about_me": request.form["about"]}}
            )
            return render_template("profile.html", user=user)
    else:
        return render_template("404.html", message="User not found. Log in first."), 404



@app.route("/send_letter", methods=["GET", "POST"])
def send_letter():
    try:
        if "userid" in session:
            userid = session["userid"]
            user = get_user(userid)

            if request.method == "GET":
                
                friends_array = []
                if 'friends' in user:
                    for friend_id_obj in user['friends']:
                        try:
                            friend = db.users.find_one({'_id': ObjectId(friend_id_obj)})
                           
                            if friend:
                                friends_array.append(friend)
                            else:
                                print(f"Friend with ID {friend_id_obj} not found in the database.")
                        except:
                            print(f"Invalid friend ID: {friend_id_obj}")
                
                return render_template("send_letter.html", friends=friends_array)
            elif request.method == "POST":
                sender_id = session["userid"]
                
                receiver_id = request.form.get("receiver_id")
 
                letter_text = request.form.get("letter_text")
                header = request.form.get("header")
                sender = get_user(sender_id)
                sender_name = sender["username"]
                receiver = get_user(receiver_id)
                
                if sender and receiver:
                    new_letter = {
                        "sender_id": ObjectId(sender_id),
                        "sender_name":sender_name,
                        "receiver_id": ObjectId(receiver_id),
                        "header":header,
                        "letter_text": letter_text,
                        "timestamp": datetime.now(),
                    }
                    letters_collection.insert_one(new_letter)
                  
                    return redirect(url_for("inbox"))
                else:
                    return jsonify({"error": "Invalid sender or receiver"}), 400
        else:
            return jsonify({"error": "User not logged in"}), 401
    except Exception as e:
        print(f"Error sending letter: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/my_friends", methods=["GET"])
def my_friends():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)

        if user:
            friends_array = []
            if 'friends' in user:
        
                for friend_id_obj in user['friends']:
                    try:
                        friend = db.users.find_one({'_id': ObjectId(friend_id_obj)})

                        if friend:
                            friends_array.append(friend)
                        else:
                            print(f"Friend with ID {friend_id_obj} not found in the database.")
                    except:
                        print(f"Invalid friend ID: {friend_id_obj}")
                
            return render_template("my_friends.html", friends = friends_array)
    else:
        return render_template("404.html", message="User not found. Log in first."), 404


@app.route("/find_friends", methods=["GET"])
def find_friends():
    if "userid" in session:
        userid = session["userid"]
        user = get_user(userid)
        all_users = get_all_users()
        if user:
            return render_template("find_friends.html")
    else:
        return render_template("404.html", message="User not found. Log in first."), 404


### SAMUEL'S STUFF - DO NOT TOUCH!

@app.route("/getUsersJson", methods=["GET"])
def get_all_users_json():
     if "userid" in session:
        userid = session["userid"]
        current_user = get_user(userid)
        all_users = get_all_users()
        users_list = []
        for user in all_users:  
            if(user != current_user):
                new_user = {**user, '_id': str(user['_id'])}
                users_list.append(new_user)
        return jsonify(users_list) 
     else:
        return render_template("404.html", message="User not found. Log in first."), 404


# Add friend && start letter 
@app.route("/findUser", methods=["POST"])
def find_user():
    try:
        user_id = request.form.get('userId')
        user_id_obj = ObjectId(user_id)
        user = db.users.find_one({'_id': user_id_obj})
        if user:
            return render_template("friend_profile.html", user=user)
        else:
            return jsonify({'result': 'Failed, but tried'})
    except Exception as e:
        print(e)
        return jsonify({'result': 'failed'})
    
    
@app.route("/add_to_friends", methods=["POST"])
def add_to_friends():
    friend_id = request.form.get('friendId')

    try:
        friend_id_obj = ObjectId(friend_id)
        friend = db.users.find_one({'_id': friend_id_obj})

        user_id = ObjectId(session["userid"])
        user = db.users.find_one({'_id': user_id})
   
        if user and friend:
            # add friend to my friend's list 
            if 'friends' not in user:
                user['friends'] = [friend_id]
                db.users.update_one({'_id': user_id}, {'$set': {'friends': user['friends']}})
                print("Friend Added")
            elif friend_id not in user['friends']:
                user['friends'].append(friend_id)
                db.users.update_one({'_id': user_id}, {'$set': {'friends': user['friends']}})
                print("Friend Added")
            else:
                print("Already Friends")

            #add me to friend's list 
            if 'friends' not in friend: #if friend does not have 'friends' as a field
                friend['friends'] = [user_id]
                db.users.update_one({"_id":friend_id}, {'$set': {'friends': friend['friends']}})
                print("I am added to their friends list")
            elif str(user_id) not in friend['friends']:
                
                friend['friends'].append(str(user_id))
               
                db.users.update_one({'_id':ObjectId(friend_id)}, {'$set': {'friends': friend['friends']} })
                
                print(" I am added as their friend")
            else:
                print("already friends")

            
            return render_template("friend_profile.html", user = friend)
        else:
            print ("User not found")
    except:
        print ("User not found")
    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

