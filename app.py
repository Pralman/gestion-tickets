import os
import sqlite3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Initialiser la base de données SQLite
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Table des tickets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            action TEXT NOT NULL,
            resolved INTEGER DEFAULT 0
        )
    """)

    # Table des commentaires
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY(ticket_id) REFERENCES tickets(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

# 📌 Route pour récupérer tous les tickets
@app.route("/tickets", methods=["GET"])
def get_tickets():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, status, action, resolved FROM tickets")
    tickets = [{"id": row[0], "name": row[1], "status": row[2], "action": row[3], "resolved": bool(row[4])} for row in cursor.fetchall()]
    
    # Ajouter les commentaires à chaque ticket
    for ticket in tickets:
        cursor.execute("SELECT text FROM comments WHERE ticket_id = ?", (ticket["id"],))
        ticket["comments"] = [{"text": row[0]} for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(tickets)

# 📌 Route pour créer un nouveau ticket
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

# 📌 Route pour marquer un ticket comme résolu
@app.route("/tickets/<int:ticket_id>", methods=["PUT"])
def resolve_ticket(ticket_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET resolved = NOT resolved WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Ticket mis à jour"}), 200

# 📌 Route pour supprimer un ticket
@app.route("/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    cursor.execute("DELETE FROM comments WHERE ticket_id = ?", (ticket_id,))  # Supprimer aussi les commentaires associés
    conn.commit()
    conn.close()
    return jsonify({"message": "Ticket supprimé"}), 200

# 📌 Route pour ajouter un commentaire à un ticket
@app.route("/tickets/<int:ticket_id>/comment", methods=["POST"])
def add_comment(ticket_id):
    data = request.json
    if not data or "comment" not in data:
        return jsonify({"error": "Données invalides"}), 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (ticket_id, text) VALUES (?, ?)", (ticket_id, data["comment"]))
    conn.commit()
    conn.close()

    return jsonify({"message": "Commentaire ajouté avec succès"}), 201

# 📌 Route pour supprimer un commentaire
@app.route("/tickets/<int:ticket_id>/comment/<int:comment_id>", methods=["DELETE"])
def delete_comment(ticket_id, comment_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE id = ? AND ticket_id = ?", (comment_id, ticket_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Commentaire supprimé"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)