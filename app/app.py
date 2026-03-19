import os
from flask import Flask, jsonify

app = Flask(__name__)

# Intentionally fail at startup if env var is missing
STRIPE_API_KEY = os.environ["STRIPE_API_KEY"]

@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "message": "Fragile app is running",
        "stripe_key_present": True
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/pay")
def pay():
    return jsonify({
        "message": "Simulated payment endpoint",
        "using_key_prefix": STRIPE_API_KEY[:6]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)