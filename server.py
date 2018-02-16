from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import datetime #time stuff
import time
import re #Regex
import md5 #hasing
import os, binascii #for hasing


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__)
mysql = MySQLConnector(app,'walls')
app.secret_key = '0118999881999119725'


@app.route('/')
def index():                         # run query with query_db()
    return render_template('index.html')

@app.route('/adduser')
def loadreg():
    if session:
        return render_template('adduser.html')
    else:
        return redirect('/logout')
@app.route('/login', methods=['POST'])
def login():

    query = "SELECT * FROM users WHERE email=:email"
    email = request.form['email']
    password = request.form['password']
    data = {
             'email': email
           }
    i = mysql.query_db(query, data)
    if(len(i)!=0):
        encrypted_password = md5.new(password + i[0]['salt']).hexdigest()
        if i[0]['password'] == encrypted_password:
            session['id']=i[0]['id']
            return redirect('/wall')
        else:
            flash("Incorrect password")
            return redirect('/')
    else:
        flash("Email not found")
        return redirect('/')   

@app.route('/register', methods=['POST'])
def create():
    if not session:
        return redirect('/logout')
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']
    

    confirm_pass=request.form['confirm_pass']

    email=request.form['email']
    birthday=request.form['birthday']

    #Validations Below
    if(len(first_name)==0):
        flash("First Name cannot be empty!")
        return redirect('/')
    elif(not first_name.isalpha()):
        flash("First Name cannot contain numbers")
        return redirect('/')
    if(len(birthday)==0):
        flash("Birthday cannot be empty!")
        return redirect('/')
    else:
        birthday = time.strptime(str(birthday), "%Y-%m-%d")
        date = datetime.date.today()
        date = time.strptime(str(date)  , "%Y-%m-%d")
        if(date < birthday):
            flash("Birthday must be in the past")
            return redirect('/')        
    if(len(last_name)==0):
        flash("Last Name cannot be empty!")
        return redirect('/')
    elif(not last_name.isalpha()):
        flash("Last Name cannot contain numbers")
        return redirect('/')

    if(len(password)==0):
        flash("Password cannot be empty!")
        return redirect('/')
    elif(len(password)<8):
        flash("Password cannot be less than 8 characters!")
        return redirect('/')
    # elif(not(any(c.isdigit() for c in password) and any(c.isupper() for c in password))):
    #     flash("Password must contain upper case letter and number")
    #     return redirect('/')

    if(len(confirm_pass)==0):
        flash("Confirm your password")
        return redirect('/')
    elif(not password == confirm_pass):
        flash("Passwords dont match")
        return redirect('/')

    if(len(email) < 1):
        flash("Email cannot be empty!")
        return redirect('/')
    elif not EMAIL_REGEX.match(email):
        flash("Invalid Email Address!") 
        return redirect('/')

        #hashing
    salt = binascii.b2a_hex(os.urandom(15))
    password = md5.new(password+salt).hexdigest()

    query = "SELECT * FROM users WHERE email=:email"
   
    #check if email exists in database already
    data = {
             'email': email
           }
    i = mysql.query_db(query, data)

    # Run query, with dictionary values injected into the query.
    query = "INSERT INTO users (first_name, last_name, email, password, salt, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, :salt, Now(), Now())" 
    if len(i)<1:
        data =  {
                    'first_name': first_name,
                    'last_name': last_name,
                    'password' : password,
                    'email': email,
                    'salt': salt
                }
        mysql.query_db(query, data)
        flash("Please login")

    else:
        flash("Email already exists")
    return redirect('/')

#Add new Comment
@app.route('/newcomment', methods=['POST'])
def newcomment():
    if not session:
        return redirect('/logout')
    
    messageid=request.form['messageid']
    comment=request.form['newcomment']
    if len(comment) < 1:
        flash("Please enter a comment")
        return redirect('/wall')
    query = "INSERT INTO comments (users_id, messages_id, comment, created_at, updated_at) VALUES (:session_id, :messages_id, :comment, Now(), Now())"
    data = {
                'session_id': session['id'],
                'messages_id' : messageid,
                'comment':comment
    }
    mysql.query_db(query, data)
    return redirect('/wall')

#Add new message
@app.route('/newmessage', methods=['POST'])
def newmessage():
    if not session:
        return redirect('/logout')
    message=request.form['newmessage']
    query = "INSERT INTO messages (users_id,  message, created_at, updated_at) VALUES (:session_id,  :message, Now(), Now())"
    data = {
                'session_id': session['id'],
                'message':message
    }
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/deletemessage', methods=['POST'])
def delmessage():
    if not session:
        return redirect('/logout')
    if(str(session['id']) == request.form['id']):
        #DELETE COMMENTS FIRST
        query = "DELETE FROM comments WHERE messages_id=:message_id"
        data={
                'message_id':request.form['messageid']
        }
        mysql.query_db(query, data)


        query = "DELETE FROM messages WHERE users_id=:user_id AND id=:message_id"
        data={
                'user_id':session['id'],
                'message_id':request.form['messageid']
        }
        mysql.query_db(query, data)
        return redirect('/wall')
    else:
        flash("BAD")
        return redirect("/")


@app.route('/wall')
def success():
    if not session:
        return redirect('/logout')
    query = "SELECT first_name, last_name, message, messages.id, DATE_FORMAT(messages.created_at, '%m/%d/%Y') as date1, users.id as user_id FROM users  JOIN messages ON users.id=messages.users_id ORDER BY messages.created_at Desc"
    result = mysql.query_db(query)                           # run query with query_db()
    msgarray = []
    print result

    #ITERATING THROUGH MESSAGES
    for x in range(0,len(result)):
        messages={ 'name':result[x]['first_name'] + " " + result[x]['last_name'],
                    'message':result[x]['message'],
                    'id':result[x]['id'],
                    'comments':[],
                    'timestamp':result[x]['date1'],
                    'user_id':result[x]['user_id']
        }
        msgarray.append(messages)

                          # run query with query_db()


    for x in range(0,len(msgarray)):
        commentsquery = "SELECT * FROM messages  JOIN comments ON messages.id=comments.messages_id WHERE messages.id=:id"
        commentsdata={
            'id':msgarray[x]['id']
        }
        commentsresult = mysql.query_db(commentsquery,commentsdata)
        for com in commentsresult:
            namequery = "SELECT CONCAT(users.first_name, ' ', users.last_name) as name,  DATE_FORMAT(comments.created_at, '%m/%d/%Y') as date1 FROM users JOIN comments ON users.id=comments.users_id WHERE comments.id=:id"
            namedata={
                'id':com['id']
            }
            nameresult=mysql.query_db(namequery, namedata)

            msgarray[x]['comments'].append(nameresult[0]['name'] + " - " + nameresult[0]['date1'] + ": " + com['comment']) 

    print msgarray
    return render_template('success.html', id=session['id'], messages=msgarray, debug=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

app.run(debug=True)
