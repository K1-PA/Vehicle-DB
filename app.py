
from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = 'bookings.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

@app.route("/vehicles")
def vehicles():
    return render_template("vehicles.html")

@app.route("/drivers")
def drivers():
    return render_template("drivers.html")

@app.route("/reports")
def reports():
    return render_template("reports.html")

@app.route("/api/productions")
def api_productions():
    conn = get_db()
    cur = conn.execute("SELECT DISTINCT date, production FROM bookings")
    rows = cur.fetchall()
    events = [{"title": row["production"], "start": row["date"]} for row in rows]
    conn.close()
    return jsonify(events)

@app.route("/api/bookings_by_date", methods=["POST"])
def api_bookings_by_date():
    date = request.json.get("date")
    conn = get_db()
    cur = conn.execute("SELECT * FROM bookings WHERE date = ?", (date,))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/drivers")
def api_drivers():
    conn = get_db()
    cur = conn.execute("SELECT id, name FROM drivers")
    drivers = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(drivers)

@app.route("/api/update_driver", methods=["POST"])
def update_driver():
    data = request.json
    booking_id = data.get("booking_id")
    new_driver = data.get("new_driver")
    conn = get_db()
    conn.execute("UPDATE bookings SET driver = ? WHERE id = ?", (new_driver, booking_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route("/api/todos")
def api_todos():
    conn = get_db()
    cur = conn.execute("SELECT * FROM todos")
    todos = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(todos)

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/add_booking", methods=["GET", "POST"])
def add_booking():
    conn = get_db()
    drivers = conn.execute("SELECT name FROM drivers").fetchall()
    if request.method == "POST":
        data = request.form
        conn.execute("""
            INSERT INTO bookings (date, production, driver, vehicle, call_time, wrap_time, location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["date"], data["production"], data["driver"], data["vehicle"],
            data["call_time"], data["wrap_time"], data["location"], data["notes"]
        ))
        conn.commit()
        conn.close()
        return render_template("success.html", message="Booking created successfully.")
    return render_template("booking_form.html", drivers=drivers, booking=None)

@app.route("/edit_booking/<int:booking_id>", methods=["GET", "POST"])
def edit_booking(booking_id):
    conn = get_db()
    drivers = conn.execute("SELECT name FROM drivers").fetchall()
    cur = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    booking = cur.fetchone()
    if request.method == "POST":
        data = request.form
        conn.execute("""
            UPDATE bookings SET date=?, production=?, driver=?, vehicle=?, call_time=?, wrap_time=?, location=?, notes=?
            WHERE id=?
        """, (
            data["date"], data["production"], data["driver"], data["vehicle"],
            data["call_time"], data["wrap_time"], data["location"], data["notes"],
            booking_id
        ))
        conn.commit()
        conn.close()
        return render_template("success.html", message="Booking updated successfully.")
    return render_template("booking_form.html", drivers=drivers, booking=booking)
