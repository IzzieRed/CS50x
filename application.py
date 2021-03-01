import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

@app.route("/")
@login_required
def index():
    id = session['user_id']
    info = db.execute("SELECT * FROM project WHERE user_id = :id AND status<>'1';", id=id)
    user = db.execute("SELECT username FROM users WHERE id = :id;", id=id)[0]['username']
    
    projects = []
    
    for row in info:
        project = row["project"]
        description = row["description"]
        deadline = row["deadline"]
        projects.append(row)
    
    return render_template("index.html", user=user, projects=projects)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure confirmation of password was submitted
        elif not request.form.get("confirm_password") == request.form.get("password"):
            return apology("passwords must match", 403)

        # Ensure password contains a number
        elif not any(c.isdigit() for c in request.form.get("password")):
            return apology("Password must contain a number.")

        # Input username/hashed password to database
        hashp = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (hash, username) VALUES(:hashp, :username)",
                   hashp=generate_password_hash(request.form.get("password")), username=request.form.get("username"))
        return redirect("/")
        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")
        
@app.route("/addnew", methods=["GET", "POST"])
@login_required
def addnew():
    if request.method == "POST":
        
        # Ensure project name was submitted
        if not request.form.get("project"):
            return apology("must provide project name", 403)
            
        # Ensure project description was submitted
        if not request.form.get("description"):
            return apology("must provide description", 403)
        
        # Ensure project deadline was submitted
        if not request.form.get("deadline"):
            return apology("must provide due date", 403)
            
        # Input Project Info to database
        id = session['user_id']
        db.execute("INSERT INTO project (project, description, deadline, user_id, status) VALUES(:project, :description, :deadline, :user_id, :status)",
                   project=request.form.get("project"), description=request.form.get("description"), deadline=request.form.get("deadline"), user_id=id, status='0')
        
        return redirect("/")
    
    else:
        return render_template("addnew.html")
    
@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        id = session['user_id']
        project = request.form.get("project")
        project_id = db.execute("SELECT project_id FROM project WHERE project=:project AND user_id=:id;", project=project, id=id)[0]['project_id']
        details = db.execute("SELECT * FROM project WHERE project_id=:project_id AND user_id=:id;", project_id=project_id, id=id)
        # if task added, insert into database    
        newtask = request.form.get("newtask")
        if newtask:
            db.execute("INSERT INTO tasks (project_id, task, details, status) VALUES (:project_id, :task, :details, :status)", 
                        project_id=project_id, task=newtask, details=request.form.get("details"), status=False)
        # show project information
        for rows in details:
            description = rows["description"]
            deadline = rows["deadline"]
        # if tasks exist, show on page
        addedtasks = db.execute("SELECT * FROM tasks WHERE project_id=:project_id;", project_id=project_id)
        added = []
        if addedtasks:
            for t in addedtasks:
                task = t["task"]
                details = t["details"]
                added.append(t)
        return render_template("edits.html", project=project, description=description, deadline=deadline, added=added)
        
    else:
        id = session['user_id']
        info = db.execute("SELECT project, project_id FROM project WHERE user_id = :id;", id=id)
        projects = []
        for row in info:
            project = row["project"]
            projects.append(row) 
        return render_template("edit.html",projects=projects)
    
@app.route("/project", methods=["POST"])
@login_required
def project():
    if request.method =="POST":
        id = session['user_id']
        project = request.form.get("project")
        project_id = db.execute("SELECT project_id FROM project WHERE project=:project AND user_id=:id;", project=project, id=id)[0]['project_id']
        details = db.execute("SELECT * FROM project WHERE project_id=:project_id AND user_id=:id;", project_id=project_id, id=id)
        # show project information
        for rows in details:
            description = rows["description"]
            deadline = rows["deadline"]
        # if tasks exist, show on page
        addedtasks = db.execute("SELECT * FROM tasks WHERE project_id=:project_id AND status='0';", project_id=project_id)
        todos = []
        if addedtasks:
            for t in addedtasks:
                task = t["task"]
                details = t["details"]
                todos.append(t)
        # if task has been ticked, change status in db
        checkbox = request.form.get("checkbox")
        if checkbox:
            for a in checkbox:
                db.execute("UPDATE tasks SET status='1' WHERE task=:task", task=checkbox)
                return render_template("project.html", project=project, description=description, deadline=deadline, todos=todos)
        if 'Finish' in request.form:
            db.execute("INSERT INTO archive VALUES(:project_id, :user_id, :project_name, :project_deadline, CURRENT_TIMESTAMP, :description);",
                       project_id=project_id, user_id=id, project_name=project, project_deadline=deadline, description=description)
            db.execute("UPDATE project SET status='1' WHERE project_id=:project_id", project_id=project_id)
            db.execute("UPDATE tasks SET status='1' WHERE project_id=:project_id", project_id=project_id)
            return redirect("/")
        else:
            return render_template("project.html", project=project, description=description, deadline=deadline, todos=todos)
    
@app.route("/archived")
@login_required
def archived():
    id = session['user_id']
    history = db.execute("SELECT project_name, project_deadline, Completed FROM archive WHERE user_id = :id;", id=id)
    return render_template("archived.html", history=history)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)