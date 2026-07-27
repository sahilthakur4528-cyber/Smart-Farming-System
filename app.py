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

    conn = get_connection()

    if conn is None:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

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

    if user is None:
        return "User not found", 404

    if profile is None:
        return "Farmer profile not found", 404

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Smart Farming Report")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(100, 780, "SMART FARMING ADVISORY SYSTEM")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 750, "Prediction Report")

    pdf.setFont("Helvetica", 11)

    pdf.drawString(
        60, 700,
        f"Farmer Name: {user['full_name']}"
    )

    pdf.drawString(
        60, 680,
        f"Village: {profile['village']}"
    )

    pdf.drawString(
        60, 660,
        f"District: {profile['district']}"
    )

    pdf.drawString(
        60, 640,
        f"State: {profile['state']}"
    )

    pdf.drawString(
        60, 620,
        f"Soil Type: {profile['soil_type']}"
    )

    pdf.drawString(
        60, 600,
        f"Land Area: {profile['land_area']} Acres"
    )

    pdf.drawString(
        60, 550,
        f"Recommended Crop: {session.get('crop', 'N/A')}"
    )

    pdf.drawString(
        60, 530,
        f"Fertilizer: {session.get('fertilizer', 'N/A')}"
    )

    pdf.drawString(
        60, 510,
        f"Quantity: {session.get('quantity', 'N/A')}"
    )

    pdf.drawString(
        60, 490,
        f"Method: {session.get('method', 'N/A')}"
    )

    pdf.drawString(
        60, 450,
        f"Nitrogen: {session.get('nitrogen', 'N/A')}"
    )

    pdf.drawString(
        60, 430,
        f"Phosphorus: {session.get('phosphorus', 'N/A')}"
    )

    pdf.drawString(
        60, 410,
        f"Potassium: {session.get('potassium', 'N/A')}"
    )

    pdf.drawString(
        60, 390,
        f"Temperature: {session.get('temperature', 'N/A')} °C"
    )

    pdf.drawString(
        60, 370,
        f"Humidity: {session.get('humidity', 'N/A')} %"
    )

    pdf.drawString(
        60, 350,
        f"Rainfall: {session.get('rainfall', 'N/A')} mm"
    )

    pdf.drawString(
        60, 330,
        f"Soil pH: {session.get('ph', 'N/A')}"
    )

    pdf.drawString(
        60, 280,
        f"Irrigation Advice: {session.get('irrigation', 'N/A')}"
    )

    pdf.drawString(
        60, 240,
        f"Generated: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}"
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
