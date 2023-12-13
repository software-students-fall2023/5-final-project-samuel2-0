
from flask import Flask,render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from werkzeug.utils import secure_filename

app = Flask(__name__)

def connection_db():
    """
    make a connection to db
    """
    return MongoClient("mongodb://localhost:27017/")

client = connection_db()
db = client["db"]
users_collection = db['users']

fake_user = {
    "_id": "1",
    "username": "johndoe",
    "name": "John Doe",
    "age": "25",
    "country": "USA",
    "interests": "Sports",
    "languages": "English"
}

def get_user(user_id):
    return users_collection.find_one({'_id': user_id})

@app.route("/")
def welcome():
    return render_template("index.html")

@app.route("/profile/<user_id>")
def myprofile(user_id):
    if(user_id == "1" and users_collection.count_documents({'_id': user_id}) == 0):
        users_collection.insert_one(fake_user)
    user = get_user(user_id)
    if user:
        return render_template("profile.html", user=user)
    else:
         return render_template("404.html", message='User not found. Log in first.'), 404

@app.route("/profile/<user_id>/edit_profile")
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
        user['username'] = request.form['username']
        user['name'] = request.form['name']
        user['age'] = request.form['age']
        user['country'] = request.form['country']
        users_collection.save(user)
        return render_template("profile.html", user=user)
    else:
       return 'User not found. Log in first.', 404

@app.route("/profile/<user_id>/edit_interests")
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
        user['interests'] = request.form['interests']
        users_collection.save(user)
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
        user['languages'] = request.form['languages']
        users_collection.save(user)
        return render_template("profile.html", user=user)
    else:
       return 'User not found. Log in first.', 404
    
@app.route("/profile/<user_id>/edit_about")
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
        user['about'] = request.form['about']
        users_collection.save(user)
        return render_template("profile.html", user=user)
    else:
       return 'User not found. Log in first.', 404

'''
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_picture/<user_id>', methods=['GET', 'POST'])
def upload_picture(user_id):
    return "good"

'''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)









