import os

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BOOKING_SERVICE_URL = os.environ.get("BOOKING_SERVICE_URL", "http://booking-service:5000")


@app.route("/")
def index():
    try:
        resp = requests.get(f"{BOOKING_SERVICE_URL}/events", timeout=5)
        events = resp.json()
    except Exception:
        events = []
    return render_template("index.html", events=events)


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
