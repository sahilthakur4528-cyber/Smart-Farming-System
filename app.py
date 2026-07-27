from flask import Flask, render_template, request, redirect, session
from database import get_connection
from predict import predict_crop
import pandas as pd

from flask import make_response
from reportlab.pdfgen import canvas
from reportlab.lib import colors      
from io import BytesIO
from datetime import datetime         
from irrigation import irrigation_advice
app = Flask(__name__)

# Secret Key
app.secret_key = "smartfarming123"


# ================= HOME =================

@app.route("/")
def home():
    return render_template("home.html")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Password and Confirm Password do not match."

        conn = get_connection()
        cursor = conn.cursor()

        # Check Email
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        email_exists = cursor.fetchone()

        if email_exists:
            conn.close()
            return "Email already registered."

        # Check Mobile
        cursor.execute("SELECT * FROM users WHERE mobile=%s", (mobile,))
        mobile_exists = cursor.fetchone()

        if mobile_exists:
            conn.close()
            return "Mobile number already registered."

        # Insert User
        cursor.execute(
            """
            INSERT INTO users(full_name,email,mobile,password)
            VALUES(%s,%s,%s,%s)
            """,
            (fullname, email, mobile, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()

        if conn is None:
            return "Database connection failed", 500

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )

        user = cursor.fetchone()

        if user:

            session["user_id"] = user["id"]

            cursor.execute(
                "SELECT * FROM farmer_profile WHERE user_id=%s",
                (user["id"],)
            )

            profile = cursor.fetchone()

            cursor.close()
            conn.close()

            if profile:
                return redirect("/dashboard")
            else:
                return redirect("/farmer_profile")

        else:
            cursor.close()
            conn.close()
            return "Invalid Email or Password"

    return render_template("login.html")

# ================= FARMER PROFILE =================

@app.route("/farmer_profile", methods=["GET", "POST"])
def farmer_profile():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        village = request.form["village"]
        district = request.form["district"]
        state = request.form["state"]
        soil = request.form["soil_type"]
        land = request.form["land_area"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO farmer_profile
            (user_id, village, district, state, soil_type, land_area)
            VALUES(%s,%s,%s,%s,%s,%s)
        """, (session["user_id"], village, district, state, soil, land))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("farmer_profile.html")


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    # User Details
    cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (session["user_id"],)
    )
    user = cursor.fetchone()

    # Farmer Profile
    cursor.execute(
        "SELECT * FROM farmer_profile WHERE user_id=%s",
        (session["user_id"],)
    )
    profile = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        profile=profile
    )

# ================= prediction =================

@app.route("/prediction", methods=["GET", "POST"])
def prediction():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        nitrogen = float(request.form["nitrogen"])
        phosphorus = float(request.form["phosphorus"])
        potassium = float(request.form["potassium"])
        temperature = float(request.form["temperature"])
        humidity = float(request.form["humidity"])
        rainfall = float(request.form["rainfall"])
        ph = float(request.form["ph"])

        # ML Crop Prediction
        crop = predict_crop(
            nitrogen,
            phosphorus,
            potassium,
            temperature,
            humidity,
            rainfall,
            ph
        )

        # ===============================
        # Irrigation Advice
        # ===============================
        irrigation = irrigation_advice(crop, rainfall)

        # ===============================
        # Read Fertilizer Dataset
        # ===============================
        df = pd.read_csv("fertilizer_dataset.csv")

        fertilizer = df[df["Crop"] == crop]

        if not fertilizer.empty:
            fertilizer_name = fertilizer.iloc[0]["Fertilizer"]
            quantity = fertilizer.iloc[0]["Quantity"]
            method = fertilizer.iloc[0]["Method"]
        else:
            fertilizer_name = "Not Available"
            quantity = "Not Available"
            method = "Not Available"

        # ===============================
        # Save Data in Session
        # ===============================
        session["crop"] = crop
        session["fertilizer"] = fertilizer_name
        session["quantity"] = quantity
        session["method"] = method
        session["irrigation"] = irrigation

        session["nitrogen"] = nitrogen
        session["phosphorus"] = phosphorus
        session["potassium"] = potassium
        session["temperature"] = temperature
        session["humidity"] = humidity
        session["rainfall"] = rainfall
        session["ph"] = ph

        # ===============================
        # Show Result
        # ===============================
        return render_template(
            "result.html",
            crop=crop,
            fertilizer=fertilizer_name,
            quantity=quantity,
            method=method,
            irrigation=irrigation
        )

    return render_template("prediction.html")


# ================= Download report =================

@app.route("/download_pdf")
def download_pdf():

    if "user_id" not in session:
        return redirect("/login")

    # Get Farmer Details
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id=%s",
        (session["user_id"],)
    )
    user = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM farmer_profile WHERE user_id=%s",
        (session["user_id"],)
    )
    profile = cursor.fetchone()

    conn.close()

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Smart Farming Report")

    # ===========================
    # OUTER BORDER
    # ===========================
    pdf.setStrokeColor(colors.darkgreen)
    pdf.setLineWidth(3)
    pdf.rect(20,20,570,800)

    # ===========================
    # HEADER
    # ===========================
    pdf.setFillColor(colors.darkgreen)
    pdf.rect(20,760,570,60,fill=1)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold",18)
    pdf.drawCentredString(
        305,
        790,
        "SMART FARMING ADVISORY SYSTEM"
    )

    pdf.setFont("Helvetica",12)
    pdf.drawCentredString(
        305,
        772,
        "Prediction Report"
    )

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica",10)

    pdf.drawRightString(
        570,
        745,
        datetime.now().strftime("%d-%m-%Y %I:%M %p")
    )

    # ===========================
    # FARMER INFORMATION
    # ===========================
    pdf.setStrokeColor(colors.green)

    pdf.roundRect(
        40,
        640,
        510,
        80,
        10
    )

    pdf.setFont("Helvetica-Bold",13)
    pdf.drawString(55,700,"Farmer Information")

    pdf.setFont("Helvetica",11)

    pdf.drawString(
        60,
        680,
        f"Farmer Name : {user['full_name']}"
    )

    pdf.drawString(
        60,
        660,
        f"Village : {profile['village']}"
    )

    pdf.drawString(
        320,
        680,
        f"Soil Type : {profile['soil_type']}"
    )

    pdf.drawString(
        320,
        660,
        f"Land Area : {profile['land_area']} Acres"
    )

    # ===========================
    # PREDICTION DETAILS
    # ===========================
    pdf.roundRect(
        40,
        520,
        510,
        90,
        10
    )

    pdf.setFont("Helvetica-Bold",13)
    pdf.drawString(
        55,
        590,
        "Prediction Details"
    )

    pdf.setFont("Helvetica",11)

    pdf.drawString(
        60,
        565,
        f"Recommended Crop : {session.get('crop')}"
    )

    pdf.drawString(
        60,
        545,
        f"Fertilizer : {session.get('fertilizer')}"
    )

    pdf.drawString(
        320,
        565,
        f"Quantity : {session.get('quantity')}"
    )

    pdf.drawString(
        320,
        545,
        f"Method : {session.get('method')}"
    )

    # ===========================
    # INPUT VALUES
    # ===========================
    pdf.roundRect(
        40,
        320,
        510,
        170,
        10
    )

    pdf.setFont("Helvetica-Bold",13)
    pdf.drawString(
        55,
        470,
        "Input Values"
    )

    pdf.setFont("Helvetica",11)

    pdf.drawString(
        60,
        445,
        f"Nitrogen : {session.get('nitrogen')}"
    )

    pdf.drawString(
        60,
        425,
        f"Phosphorus : {session.get('phosphorus')}"
    )

    pdf.drawString(
        60,
        405,
        f"Potassium : {session.get('potassium')}"
    )

    pdf.drawString(
        60,
        385,
        f"Temperature : {session.get('temperature')} °C"
    )

    pdf.drawString(
        320,
        445,
        f"Humidity : {session.get('humidity')} %"
    )

    pdf.drawString(
        320,
        425,
        f"Rainfall : {session.get('rainfall')} mm"
    )

    pdf.drawString(
        320,
        405,
        f"Soil pH : {session.get('ph')}"
    )

    # ===========================
    # RECOMMENDATION
    # ===========================
    pdf.setFillColor(colors.lightgreen)

    pdf.roundRect(
    40,
    190,
    510,
    100,
    10,
    fill=1
)

    pdf.setFillColor(colors.black)

    pdf.setFont("Helvetica-Bold",13)
    pdf.drawString(
        55,
        265,
        "Recommendation"
    )

    pdf.setFont("Helvetica",11)

    pdf.drawString(
        60,
        245,
        f"Recommended Crop : {session.get('crop')}"
    )

    pdf.drawString(
        60,
        225,
        f"Use Fertilizer : {session.get('fertilizer')}"
    )

    pdf.drawString(
    60,
    205,
    f"Irrigation Advice : {session.get('irrigation')}"
)

    # ===========================
    # FOOTER
    # ===========================
    pdf.setFont("Helvetica",10)

    pdf.drawCentredString(
        305,
        150,
        "Thank You for Using Smart Farming Advisory System"
    )

    pdf.drawCentredString(
        305,
        132,
        "Wishing You a Healthy Crop and Good Harvest!"
    )

    pdf.line(
        50,
        118,
        540,
        118
    )

    pdf.drawCentredString(
        305,
        100,
        "Generated by Smart Farming Advisory System"
    )

    pdf.save()

    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)

    response.headers["Content-Type"] = "application/pdf"

    response.headers["Content-Disposition"] = (
        "attachment; filename=Smart_Farming_Report.pdf"
    )

    return response

# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ================= MAIN =================

if __name__ == "__main__":
    app.run(debug=True)
