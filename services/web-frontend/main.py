import os

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BOOKING_SERVICE_URL = os.environ.get("BOOKING_SERVICE_URL", "http://booking-service:5000")

EVENTS = [
    {"id": "evt-001", "name": "Dublin Tech Summit", "venue": "RDS Arena, Dublin", "date": "2026-06-14", "price": 49.00, "available": 200},
    {"id": "evt-002", "name": "Cork Jazz Festival", "venue": "Fitzgerald Park, Cork", "date": "2026-07-20", "price": 25.00, "available": 500},
    {"id": "evt-003", "name": "Galway Comedy Night", "venue": "Roisin Dubh, Galway", "date": "2026-08-03", "price": 18.00, "available": 80},
    {"id": "evt-004", "name": "Belfast Film Fest", "venue": "QFT, Belfast", "date": "2026-09-12", "price": 12.00, "available": 150},
    {"id": "evt-005", "name": "Limerick Startup Day", "venue": "Limerick Institute", "date": "2026-10-01", "price": 0.00, "available": 300},
]


@app.route("/")
def index():
    return render_template("index.html", events=EVENTS)


@app.route("/book", methods=["POST"])
def book():
    event_id = request.form.get("event_id")
    customer_id = request.form.get("customer_id", "guest")
    try:
        resp = requests.post(
            f"{BOOKING_SERVICE_URL}/bookings",
            json={"event_id": event_id, "customer_id": customer_id},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        return jsonify({"booking_id": data["booking_id"], "status": data.get("status", "held")})
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "booking-service unavailable"}), 503
    except requests.exceptions.HTTPError as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/status/<booking_id>")
def status(booking_id):
    try:
        resp = requests.get(f"{BOOKING_SERVICE_URL}/bookings/{booking_id}", timeout=5)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "booking-service unavailable"}), 503
    except requests.exceptions.HTTPError as exc:
        return jsonify({"error": str(exc)}), 502


@app.route("/healthz")
def healthz():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
