from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from auth import auth_bp, login_required, init_db

app = Flask(_name_)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
DATABASE = 'bookings.db'

# Register authentication blueprint
app.register_blueprint(auth_bp)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
@login_required
def index():
    return render_template("index.html", username=session.get('username'))

@app.route("/calendar")
@login_required
def calendar():
    return render_template("calendar.html", username=session.get('username'))

@app.route("/vehicles")
@login_required
def vehicles():
    return render_template("vehicles.html", username=session.get('username'))

@app.route("/drivers")
@login_required
def drivers():
    return render_template("drivers.html", username=session.get('username'))

@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html", username=session.get('username'))

@app.route("/api/productions")
@login_required
def api_productions():
    conn = get_db()
    try:
        cur = conn.execute("SELECT DISTINCT date, production FROM bookings")
        rows = cur.fetchall()
        events = [{"title": row["production"], "start": row["date"]} for row in rows]
        return jsonify(events)
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/bookings_by_date", methods=["POST"])
@login_required
def api_bookings_by_date():
    date = request.json.get("date")
    conn = get_db()
    try:
        cur = conn.execute("SELECT * FROM bookings WHERE date = ?", (date,))
        rows = [dict(row) for row in cur.fetchall()]
        return jsonify(rows)
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/drivers")
@login_required
def api_drivers():
    conn = get_db()
    try:
        cur = conn.execute("SELECT id, name FROM drivers")
        drivers = [dict(row) for row in cur.fetchall()]
        return jsonify(drivers)
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/update_driver", methods=["POST"])
@login_required
def update_driver():
    data = request.json
    booking_id = data.get("booking_id")
    new_driver = data.get("new_driver")
    conn = get_db()
    try:
        conn.execute("UPDATE bookings SET driver = ? WHERE id = ?", (new_driver, booking_id))
        conn.commit()
        return jsonify({"status": "success"})
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/todos")
@login_required
def api_todos():
    conn = get_db()
    try:
        cur = conn.execute("SELECT * FROM todos")
        todos = [dict(row) for row in cur.fetchall()]
        return jsonify(todos)
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/add_booking", methods=["GET", "POST"])
@login_required
def add_booking():
    conn = get_db()
    try:
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
            flash("Booking created successfully.")
            return redirect(url_for("index"))
            
        return render_template("booking_form.html", drivers=drivers, booking=None, username=session.get('username'))
    except sqlite3.Error as e:
        flash(f"Error: {str(e)}")
        return render_template("booking_form.html", drivers=drivers, booking=None, username=session.get('username'))
    finally:
        conn.close()

@app.route("/edit_booking/<int:booking_id>", methods=["GET", "POST"])
@login_required
def edit_booking(booking_id):
    conn = get_db()
    try:
        drivers = conn.execute("SELECT name FROM drivers").fetchall()
        cur = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        booking = cur.fetchone()
        
        if booking is None:
            flash("Booking not found.")
            return redirect(url_for("index"))
            
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
            flash("Booking updated successfully.")
            return redirect(url_for("index"))
            
        return render_template("booking_form.html", drivers=drivers, booking=booking, username=session.get('username'))
    except sqlite3.Error as e:
        flash(f"Error: {str(e)}")
        return render_template("booking_form.html", drivers=drivers, booking=booking, username=session.get('username'))
    finally:
        conn.close()

if _name_ == "_main_":
    # Initialize database with users table and default admin
    init_db()
    app.run(debug=True)
