print("Flask démarre...")

import os
import sqlite3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Création de la base de données et de la table
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            action TEXT NOT NULL,
            resolved INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/tickets", methods=["GET"])
def get_tickets():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, status, action, resolved FROM tickets")
    tickets = [{"id": row[0], "name": row[1], "status": row[2], "action": row[3], "resolved": bool(row[4])} for row in cursor.fetchall()]
    conn.close()
    return jsonify(tickets)

@app.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.json
    if not data or "name" not in data or "status" not in data or "action" not in data:
        return jsonify({"error": "Données invalides"}), 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tickets (name, status, action) VALUES (?, ?, ?)", (data["name"], data["status"], data["action"]))
    conn.commit()
    new_ticket_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": new_ticket_id, "name": data["name"], "status": data["status"], "action": data["action"], "resolved": False}), 201

@app.route("/tickets/<int:ticket_id>", methods=["PUT"])
def resolve_ticket(ticket_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET resolved = NOT resolved WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Ticket mis à jour"}), 200

@app.route("/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Ticket supprimé"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
