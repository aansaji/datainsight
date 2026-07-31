from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
    jsonify
)

from openpyxl import Workbook

import sqlite3
import os
import pandas as pd

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from werkzeug.utils import secure_filename


# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = "datainsight_secret_key"

DATABASE = "database.db"

UPLOAD_FOLDER = "static/uploads"

ALLOWED_EXTENSIONS = {"csv"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# CHECK ALLOWED FILE
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# READ CSV HELPER
# =========================================================

def read_csv_file(filepath):

    try:

        return pd.read_csv(filepath)

    except UnicodeDecodeError:

        try:

            return pd.read_csv(
                filepath,
                encoding="latin-1"
            )

        except:

            return pd.read_csv(
                filepath,
                encoding="cp1252"
            )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    cursor = conn.cursor()

    # -----------------------------------------------------
    # Latest upload
    # -----------------------------------------------------

    latest_upload = cursor.execute("""
        SELECT *
        FROM uploads
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        session["user_id"],
    )).fetchone()

    latest_analysis = None

    if latest_upload:

        latest_analysis = cursor.execute("""
            SELECT *
            FROM analysis
            WHERE upload_id = ?
        """, (
            latest_upload["id"],
        )).fetchone()

    # -----------------------------------------------------
    # Dashboard statistics
    # -----------------------------------------------------

    stats = cursor.execute("""
        SELECT
            COUNT(*) AS total_uploads,
            COALESCE(SUM(rows), 0) AS total_rows,
            COALESCE(SUM(columns), 0) AS total_columns,
            COALESCE(SUM(file_size), 0) AS total_size
        FROM uploads
        WHERE user_id = ?
    """, (
        session["user_id"],
    )).fetchone()

    stats = dict(stats)

    stats["total_size"] = round(
        stats["total_size"],
        2
    )

    conn.close()

    return render_template(
        "dashboard.html",
        user=session["user_name"],
        upload=latest_upload,
        analysis=latest_analysis,
        stats=stats
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        conn = get_db_connection()

        cursor = conn.cursor()

        existing = cursor.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (
            email,
        )).fetchone()

        if existing:

            flash(
                "Email already exists.",
                "danger"
            )

            conn.close()

            return redirect(
                url_for("register")
            )

        hashed = generate_password_hash(
            password
        )

        cursor.execute("""
            INSERT INTO users(
                name,
                email,
                password
            )
            VALUES (?, ?, ?)
        """, (
            name,
            email,
            hashed
        ))

        conn.commit()

        conn.close()

        flash(
            "Registration Successful",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        conn = get_db_connection()

        cursor = conn.cursor()

        user = cursor.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (
            email,
        )).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]

            flash(
                "Login Successful",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid Email or Password",
            "danger"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged Out Successfully",
        "success"
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# UPLOAD CSV DATASET
# =========================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if "csv_file" not in request.files:

        flash(
            "No file selected.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    file = request.files["csv_file"]

    if file.filename == "":

        flash(
            "Please choose a CSV file.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    if not allowed_file(file.filename):

        flash(
            "Only CSV files are allowed.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    # -----------------------------------------------------
    # Save file
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    # -----------------------------------------------------
    # Read CSV
    # -----------------------------------------------------

    try:

        df = read_csv_file(
            filepath
        )

    except Exception as e:

        if os.path.exists(filepath):

            os.remove(filepath)

        flash(
            f"Error reading CSV: {e}",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    # -----------------------------------------------------
    # Dataset statistics
    # -----------------------------------------------------

    total_rows = len(df)

    total_columns = len(
        df.columns
    )

    missing_values = int(
        df.isnull()
        .sum()
        .sum()
    )

    duplicate_rows = int(
        df.duplicated()
        .sum()
    )

    # -----------------------------------------------------
    # Numeric statistics
    # -----------------------------------------------------

    numeric = df.select_dtypes(
        include="number"
    )

    if numeric.empty:

        average = 0

        maximum = 0

        minimum = 0

        median = 0

    else:

        average = float(
            numeric.mean()
            .mean()
        )

        maximum = float(
            numeric.max()
            .max()
        )

        minimum = float(
            numeric.min()
            .min()
        )

        median = float(
            numeric.median()
            .median()
        )

    # -----------------------------------------------------
    # Database connection
    # -----------------------------------------------------

    conn = get_db_connection()

    cursor = conn.cursor()

    file_size = round(
        os.path.getsize(filepath) / 1024,
        2
    )

    # -----------------------------------------------------
    # Save upload
    # -----------------------------------------------------

    cursor.execute("""
        INSERT INTO uploads(
            user_id,
            filename,
            filepath,
            file_size,
            rows,
            columns
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        filename,
        filepath,
        file_size,
        total_rows,
        total_columns
    ))

    upload_id = cursor.lastrowid

    # -----------------------------------------------------
    # Save analysis
    # -----------------------------------------------------

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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
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

    flash(
        "Dataset uploaded successfully!",
        "success"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# UPLOAD HISTORY
# =========================================================

@app.route("/history")
def history():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    search = request.args.get(
        "search",
        ""
    )

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
        AND uploads.filename LIKE ?
        ORDER BY uploads.upload_date DESC
    """, (
        session["user_id"],
        "%" + search + "%"
    )).fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=history,
        user=session["user_name"],
        search=search
    )


# =========================================================
# VIEW DATASET
# =========================================================

@app.route(
    "/view/<int:upload_id>"
)
def view_dataset(upload_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    upload = conn.execute("""
        SELECT *
        FROM uploads
        WHERE id = ?
        AND user_id = ?
    """, (
        upload_id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if upload is None:

        flash(
            "Dataset not found.",
            "danger"
        )

        return redirect(
            url_for("history")
        )

    # -----------------------------------------------------
    # Read CSV
    # -----------------------------------------------------

    try:

        df = read_csv_file(
            upload["filepath"]
        )

    except Exception as e:

        flash(
            f"Unable to read dataset: {e}",
            "danger"
        )

        return redirect(
            url_for("history")
        )

    # -----------------------------------------------------
    # Basic information
    # -----------------------------------------------------

    total_rows = len(df)

    total_columns = len(
        df.columns
    )

    missing_values = int(
        df.isnull()
        .sum()
        .sum()
    )

    duplicate_rows = int(
        df.duplicated()
        .sum()
    )

    # -----------------------------------------------------
    # Column types
    # -----------------------------------------------------

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        exclude="number"
    ).columns.tolist()

    all_columns = [
        str(column)
        for column in df.columns
    ]

    # -----------------------------------------------------
    # Numeric statistics
    # -----------------------------------------------------

    statistics = []

    for column in numeric_columns:

        column_data = (
            df[column]
            .dropna()
        )

        if len(column_data) > 0:

            statistics.append({

                "column": str(column),

                "average": round(
                    float(
                        column_data.mean()
                    ),
                    2
                ),

                "maximum": round(
                    float(
                        column_data.max()
                    ),
                    2
                ),

                "minimum": round(
                    float(
                        column_data.min()
                    ),
                    2
                ),

                "median": round(
                    float(
                        column_data.median()
                    ),
                    2
                )
            })

    # -----------------------------------------------------
    # Dataset preview
    # -----------------------------------------------------

    table = df.head(20).to_html(
        classes="dataset-table",
        index=False,
        border=0
    )

    # -----------------------------------------------------
    # Automatic insights
    # -----------------------------------------------------

    insights = []

    if total_rows > 10000:

        insights.append(
            "This is a large dataset suitable for advanced analysis."
        )

    elif total_rows > 1000:

        insights.append(
            "This is a medium-sized dataset with enough records for meaningful analysis."
        )

    else:

        insights.append(
            "This is a relatively small dataset."
        )

    if missing_values == 0:

        insights.append(
            "Excellent data completeness: no missing values were detected."
        )

    else:

        insights.append(
            f"The dataset contains {missing_values} missing values."
        )

    if duplicate_rows == 0:

        insights.append(
            "No duplicate rows were detected."
        )

    else:

        insights.append(
            f"{duplicate_rows} duplicate rows were detected."
        )

    if numeric_columns:

        insights.append(
            f"{len(numeric_columns)} numeric column(s) are available for statistical analysis."
        )

    if categorical_columns:

        insights.append(
            f"{len(categorical_columns)} categorical column(s) are available for filtering and grouping."
        )

    return render_template(
        "view_dataset.html",

        filename=upload["filename"],

        upload_id=upload_id,

        rows=total_rows,

        columns=total_columns,

        missing_values=missing_values,

        duplicate_rows=duplicate_rows,

        table=table,

        all_columns=all_columns,

        numeric_columns=numeric_columns,

        categorical_columns=categorical_columns,

        statistics=statistics,

        insights=insights
    )


# =========================================================
# DATASET DATA API
# =========================================================

@app.route(
    "/dataset-data/<int:upload_id>"
)
def dataset_data(upload_id):

    if "user_id" not in session:

        return jsonify({
            "error": "Unauthorized"
        }), 401

    conn = get_db_connection()

    upload = conn.execute("""
        SELECT *
        FROM uploads
        WHERE id = ?
        AND user_id = ?
    """, (
        upload_id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if upload is None:

        return jsonify({
            "error": "Dataset not found"
        }), 404

    # -----------------------------------------------------
    # Read CSV
    # -----------------------------------------------------

    try:

        df = read_csv_file(
            upload["filepath"]
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    # -----------------------------------------------------
    # Clean column names
    # -----------------------------------------------------

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # -----------------------------------------------------
    # Identify numeric/categorical columns
    # -----------------------------------------------------

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        exclude="number"
    ).columns.tolist()

    # -----------------------------------------------------
    # Convert dates where possible
    # -----------------------------------------------------

    date_columns = []

    for column in df.columns:

        if df[column].dtype == "object":

            sample = df[column].dropna()

            if len(sample) > 0:

                converted = pd.to_datetime(
                    sample,
                    errors="coerce"
                )

                if (
                    converted.notna()
                    .mean()
                    >= 0.8
                ):

                    date_columns.append(
                        column
                    )

    # -----------------------------------------------------
    # Send first 1000 records
    # -----------------------------------------------------

    chart_df = df.head(1000).copy()

    # Convert datetime values to strings

    for column in chart_df.columns:

        if pd.api.types.is_datetime64_any_dtype(
            chart_df[column]
        ):

            chart_df[column] = (
                chart_df[column]
                .dt.strftime(
                    "%Y-%m-%d"
                )
            )

    chart_df = chart_df.fillna("")

    # -----------------------------------------------------
    # Convert special values
    # -----------------------------------------------------

    data = chart_df.to_dict(
        orient="records"
    )

    return jsonify({

        "filename": upload["filename"],

        "columns": [
            str(column)
            for column in df.columns
        ],

        "numeric_columns": [
            str(column)
            for column in numeric_columns
        ],

        "categorical_columns": [
            str(column)
            for column in categorical_columns
        ],

        "date_columns": [
            str(column)
            for column in date_columns
        ],

        "data": data,

        "rows": int(
            len(df)
        ),

        "columns_count": int(
            len(df.columns)
        ),

        "missing": int(
            df.isnull()
            .sum()
            .sum()
        ),

        "duplicates": int(
            df.duplicated()
            .sum()
        )

    })


# =========================================================
# DELETE DATASET
# =========================================================

@app.route(
    "/delete/<int:upload_id>"
)
def delete_dataset(upload_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    cursor = conn.cursor()

    upload = cursor.execute("""
        SELECT *
        FROM uploads
        WHERE id = ?
        AND user_id = ?
    """, (
        upload_id,
        session["user_id"]
    )).fetchone()

    if upload is None:

        conn.close()

        flash(
            "Dataset not found.",
            "danger"
        )

        return redirect(
            url_for("history")
        )

    # -----------------------------------------------------
    # Delete CSV
    # -----------------------------------------------------

    if (
        upload["filepath"]
        and os.path.exists(
            upload["filepath"]
        )
    ):

        os.remove(
            upload["filepath"]
        )

    # -----------------------------------------------------
    # Delete analysis
    # -----------------------------------------------------

    cursor.execute("""
        DELETE FROM analysis
        WHERE upload_id = ?
    """, (
        upload_id,
    ))

    # -----------------------------------------------------
    # Delete upload
    # -----------------------------------------------------

    cursor.execute("""
        DELETE FROM uploads
        WHERE id = ?
    """, (
        upload_id,
    ))

    conn.commit()

    conn.close()

    flash(
        "Dataset deleted successfully!",
        "success"
    )

    return redirect(
        url_for("history")
    )


# =========================================================
# EXPORT ANALYSIS TO EXCEL
# =========================================================

@app.route(
    "/export/excel/<int:upload_id>"
)
def export_excel(upload_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    upload = conn.execute("""
        SELECT *
        FROM uploads
        WHERE id = ?
        AND user_id = ?
    """, (
        upload_id,
        session["user_id"]
    )).fetchone()

    if upload is None:

        conn.close()

        flash(
            "Dataset not found.",
            "danger"
        )

        return redirect(
            url_for("history")
        )

    analysis = conn.execute("""
        SELECT *
        FROM analysis
        WHERE upload_id = ?
    """, (
        upload_id,
    )).fetchone()

    conn.close()

    workbook = Workbook()

    sheet = workbook.active

    sheet.title = "Analysis Report"

    sheet.append([
        "DataInsight Analysis Report"
    ])

    sheet.append([])

    sheet.append([
        "Filename",
        upload["filename"]
    ])

    sheet.append([
        "Rows",
        upload["rows"]
    ])

    sheet.append([
        "Columns",
        upload["columns"]
    ])

    sheet.append([
        "File Size (KB)",
        upload["file_size"]
    ])

    sheet.append([])

    sheet.append([
        "Average",
        analysis["average"]
    ])

    sheet.append([
        "Maximum",
        analysis["maximum"]
    ])

    sheet.append([
        "Minimum",
        analysis["minimum"]
    ])

    sheet.append([
        "Median",
        analysis["median"]
    ])

    sheet.append([
        "Missing Values",
        analysis["missing_values"]
    ])

    sheet.append([
        "Duplicate Rows",
        analysis["duplicate_rows"]
    ])

    filename = (
        f"Analysis_{upload_id}.xlsx"
    )

    filepath = os.path.join(
        "static",
        filename
    )

    workbook.save(
        filepath
    )

    return send_file(
        filepath,
        as_attachment=True
    )


# =========================================================
# EXPORT ORIGINAL CSV AS XLSX
# =========================================================

@app.route(
    "/export/xlsx/<int:upload_id>"
)
def export_xlsx(upload_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    upload = conn.execute("""
        SELECT *
        FROM uploads
        WHERE id = ?
        AND user_id = ?
    """, (
        upload_id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if upload is None:

        flash(
            "Dataset not found.",
            "danger"
        )

        return redirect(
            url_for("history")
        )

    # -----------------------------------------------------
    # Read original CSV
    # -----------------------------------------------------

    try:

        df = read_csv_file(
            upload["filepath"]
        )

    except Exception as e:

        flash(
            f"Unable to export dataset: {e}",
            "danger"
        )

        return redirect(
            url_for(
                "view_dataset",
                upload_id=upload_id
            )
        )

    # -----------------------------------------------------
    # XLSX filename
    # -----------------------------------------------------

    original_name = os.path.splitext(
        upload["filename"]
    )[0]

    xlsx_filename = (
        original_name
        + ".xlsx"
    )

    xlsx_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        xlsx_filename
    )

    # -----------------------------------------------------
    # Export
    # -----------------------------------------------------

    df.to_excel(
        xlsx_path,
        index=False,
        engine="openpyxl"
    )

    return send_file(
        xlsx_path,
        as_attachment=True,
        download_name=xlsx_filename,
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# =========================================================
# EXPORT ANALYSIS TO PDF
# =========================================================

@app.route(
    "/export/pdf/<int:upload_id>"
)
def export_pdf(upload_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    upload = conn.execute("""
        SELECT *
        FROM uploads
        WHERE id = ?
        AND user_id = ?
    """, (
        upload_id,
        session["user_id"]
    )).fetchone()

    if upload is None:

        conn.close()

        flash(
            "Dataset not found.",
            "danger"
        )

        return redirect(
            url_for("history")
        )

    analysis = conn.execute("""
        SELECT *
        FROM analysis
        WHERE upload_id = ?
    """, (
        upload_id,
    )).fetchone()

    conn.close()

    pdf_path = os.path.join(
        "static",
        f"Analysis_{upload_id}.pdf"
    )

    doc = SimpleDocTemplate(
        pdf_path
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "<b>DataInsight Analysis Report</b>",
            styles["Title"]
        )
    )

    data = [

        [
            "Filename",
            upload["filename"]
        ],

        [
            "Rows",
            upload["rows"]
        ],

        [
            "Columns",
            upload["columns"]
        ],

        [
            "File Size (KB)",
            upload["file_size"]
        ],

        [
            "Average",
            analysis["average"]
        ],

        [
            "Maximum",
            analysis["maximum"]
        ],

        [
            "Minimum",
            analysis["minimum"]
        ],

        [
            "Median",
            analysis["median"]
        ],

        [
            "Missing Values",
            analysis["missing_values"]
        ],

        [
            "Duplicate Rows",
            analysis["duplicate_rows"]
        ]

    ]

    table = Table(data)

    table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightblue
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black
            ),

            (
                "BACKGROUND",
                (0, 1),
                (0, -1),
                colors.lightgrey
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, 0),
                10
            )

        ])
    )

    elements.append(
        table
    )

    doc.build(
        elements
    )

    return send_file(
        pdf_path,
        as_attachment=True
    )


# =========================================================
# USER PROFILE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    user = conn.execute("""
        SELECT
            id,
            name,
            email,
            created_at
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    uploads = conn.execute("""
        SELECT
            COUNT(*) AS total_uploads
        FROM uploads
        WHERE user_id = ?
    """, (
        session["user_id"],
    )).fetchone()

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        uploads=uploads
    )


# =========================================================
# DOWNLOAD CLEANED DATASET
# =========================================================

@app.route(
    "/clean/<int:upload_id>"
)
def clean_dataset(upload_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    upload = conn.execute("""
        SELECT *
        FROM uploads
        WHERE id = ?
        AND user_id = ?
    """, (
        upload_id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if upload is None:

        flash(
            "Dataset not found.",
            "danger"
        )

        return redirect(
            url_for("history")
        )

    try:

        df = read_csv_file(
            upload["filepath"]
        )

    except Exception as e:

        flash(
            f"Unable to read dataset: {e}",
            "danger"
        )

        return redirect(
            url_for(
                "view_dataset",
                upload_id=upload_id
            )
        )

    # -----------------------------------------------------
    # Remove duplicate rows
    # -----------------------------------------------------

    df = df.drop_duplicates()

    # -----------------------------------------------------
    # Fill missing values
    # -----------------------------------------------------

    for column in df.columns:

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):

            if not df[column].dropna().empty:

                df[column] = (
                    df[column]
                    .fillna(
                        df[column].mean()
                    )
                )

            else:

                df[column] = (
                    df[column]
                    .fillna(0)
                )

        else:

            df[column] = (
                df[column]
                .fillna("Unknown")
            )

    # -----------------------------------------------------
    # Save cleaned dataset
    # -----------------------------------------------------

    cleaned_filename = (
        "cleaned_"
        + upload["filename"]
    )

    cleaned_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        cleaned_filename
    )

    df.to_csv(
        cleaned_path,
        index=False
    )

    flash(
        "Dataset cleaned successfully!",
        "success"
    )

    return send_file(
        cleaned_path,
        as_attachment=True
    )


# =========================================================
# AI INSIGHTS
# =========================================================

@app.route(
    "/insights/<int:upload_id>"
)
def insights(upload_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    upload = conn.execute("""
        SELECT *
        FROM uploads
        WHERE id = ?
        AND user_id = ?
    """, (
        upload_id,
        session["user_id"]
    )).fetchone()

    if upload is None:

        conn.close()

        flash(
            "Dataset not found.",
            "danger"
        )

        return redirect(
            url_for("history")
        )

    analysis = conn.execute("""
        SELECT *
        FROM analysis
        WHERE upload_id = ?
    """, (
        upload_id,
    )).fetchone()

    conn.close()

    insights = []

    # -----------------------------------------------------
    # Dataset size
    # -----------------------------------------------------

    if analysis["total_records"] > 10000:

        insights.append(
            "Large dataset suitable for advanced analysis."
        )

    else:

        insights.append(
            "Small to medium sized dataset."
        )

    # -----------------------------------------------------
    # Missing values
    # -----------------------------------------------------

    if analysis["missing_values"] == 0:

        insights.append(
            "No missing values found."
        )

    elif analysis["missing_values"] < 20:

        insights.append(
            "Very few missing values detected."
        )

    else:

        insights.append(
            "Dataset contains many missing values. Cleaning is recommended."
        )

    # -----------------------------------------------------
    # Duplicate rows
    # -----------------------------------------------------

    if analysis["duplicate_rows"] == 0:

        insights.append(
            "No duplicate rows detected."
        )

    else:

        insights.append(
            f"{analysis['duplicate_rows']} duplicate rows found."
        )

    # -----------------------------------------------------
    # Overall recommendation
    # -----------------------------------------------------

    if (
        analysis["missing_values"] < 20
        and analysis["duplicate_rows"] == 0
    ):

        insights.append(
            "Overall data quality is excellent."
        )

    else:

        insights.append(
            "Run the Clean Dataset feature before further analysis."
        )

    return render_template(
        "insights.html",
        upload=upload,
        analysis=analysis,
        insights=insights
    )


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )