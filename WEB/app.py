from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

import sqlite3
import os
import pandas as pd

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename


# -----------------------------
# Flask Configuration
# -----------------------------
app = Flask(__name__)

app.secret_key = "datainsight_secret_key"

DATABASE = "database.db"

UPLOAD_FOLDER = "static/uploads"

ALLOWED_EXTENSIONS = {"csv"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------------
# Database Connection
# -----------------------------
def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# -----------------------------
# Check Allowed File
# -----------------------------
def allowed_file(filename):

    return "." in filename and \
           filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/")
def dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    conn = get_db_connection()

    cursor = conn.cursor()

    latest_upload = cursor.execute("""
        SELECT *
        FROM uploads
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
    """,(session["user_id"],)).fetchone()

    latest_analysis = None

    if latest_upload:

        latest_analysis = cursor.execute("""
            SELECT *
            FROM analysis
            WHERE upload_id=?
        """,(latest_upload["id"],)).fetchone()

    conn.close()

    return render_template(
        "dashboard.html",
        user=session["user_name"],
        upload=latest_upload,
        analysis=latest_analysis
    )


# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method=="POST":

        name=request.form["name"]

        email=request.form["email"]

        password=request.form["password"]

        conn=get_db_connection()

        cursor=conn.cursor()

        existing=cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing:

            flash("Email already exists.","danger")

            conn.close()

            return redirect(url_for("register"))

        hashed=generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users(
                name,
                email,
                password
            )
            VALUES(?,?,?)
        """,(name,email,hashed))

        conn.commit()

        conn.close()

        flash("Registration Successful","success")

        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login",methods=["GET","POST"])

def login():

    if request.method=="POST":

        email=request.form["email"]

        password=request.form["password"]

        conn=get_db_connection()

        cursor=conn.cursor()

        user=cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"]=user["id"]

            session["user_name"]=user["name"]

            flash("Login Successful","success")

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password","danger")

    return render_template("login.html")


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully","success")

    return redirect(url_for("login"))

# -----------------------------
# Run Application
# -----------------------------


 # -----------------------------
# Upload CSV Dataset
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if "csv_file" not in request.files:
        flash("No file selected.", "danger")
        return redirect(url_for("dashboard"))

    file = request.files["csv_file"]

    if file.filename == "":
        flash("Please choose a CSV file.", "danger")
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename):
        flash("Only CSV files are allowed.", "danger")
        return redirect(url_for("dashboard"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(filepath)

    # Read CSV
    try:

        try:
            df = pd.read_csv(filepath)

        except UnicodeDecodeError:
            try:
                df = pd.read_csv(filepath, encoding="latin-1")
            except:
                df = pd.read_csv(filepath, encoding="cp1252")

    except Exception as e:

        flash(f"Error reading CSV: {e}", "danger")

        return redirect(url_for("dashboard"))
    

    total_rows = len(df)

    total_columns = len(df.columns)

    missing_values = int(df.isnull().sum().sum())

    duplicate_rows = int(df.duplicated().sum())

    numeric = df.select_dtypes(include="number")

    if numeric.empty:

        average = 0
        maximum = 0
        minimum = 0
        median = 0

    else:

        average = float(numeric.mean().mean())

        maximum = float(numeric.max().max())

        minimum = float(numeric.min().min())

        median = float(numeric.median().median())   

        conn = get_db_connection()

    cursor = conn.cursor()

    file_size = round(os.path.getsize(filepath) / 1024, 2)

    cursor.execute("""
        INSERT INTO uploads(
            user_id,
            filename,
            filepath,
            file_size,
            rows,
            columns
        )
        VALUES(?,?,?,?,?,?)
    """, (

        session["user_id"],
        filename,
        filepath,
        file_size,
        total_rows,
        total_columns

    ))

    upload_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO analysis(

            upload_id,
            total_records,
            total_columns,
            average,
            maximum,
            minimum,
            median,
            missing_values,
            duplicate_rows

        )
        VALUES(?,?,?,?,?,?,?,?,?)

    """,(

        upload_id,
        total_rows,
        total_columns,
        average,
        maximum,
        minimum,
        median,
        missing_values,
        duplicate_rows

    ))

    conn.commit()

    conn.close()

    flash("Dataset uploaded successfully!", "success")

    return redirect(url_for("dashboard"))
# -----------------------------
# Upload History
# -----------------------------
@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    history = cursor.execute("""
        SELECT
            uploads.id,
            uploads.filename,
            uploads.file_size,
            uploads.rows,
            uploads.columns,
            uploads.upload_date,
            analysis.average,
            analysis.maximum,
            analysis.minimum,
            analysis.median
        FROM uploads
        LEFT JOIN analysis
        ON uploads.id = analysis.upload_id
        WHERE uploads.user_id = ?
        ORDER BY uploads.upload_date DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=history,
        user=session["user_name"]
    )

# -----------------------------
# View Dataset
# -----------------------------
@app.route("/view/<int:upload_id>")
def view_dataset(upload_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    upload = cursor.execute("""
        SELECT *
        FROM uploads
        WHERE id=? AND user_id=?
    """, (upload_id, session["user_id"])).fetchone()

    conn.close()

    if upload is None:
        flash("Dataset not found.", "danger")
        return redirect(url_for("history"))

    # Read the CSV
    try:
        df = pd.read_csv(upload["filepath"])
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(upload["filepath"], encoding="latin-1")
        except:
            df = pd.read_csv(upload["filepath"], encoding="cp1252")

    table = df.head(20).to_html(
        classes="table table-bordered",
        index=False
    )

    return render_template(
        "view_dataset.html",
        filename=upload["filename"],
        rows=len(df),
        columns=len(df.columns),
        table=table
    )


if __name__ == "__main__":
    app.run(debug=True)
