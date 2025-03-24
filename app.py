import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ✅ Base persistante sur Render
DATABASE_PATH = os.getenv("DATABASE_PATH", "/opt/render/project/persistent/database.db")

def init_db():
    if not os.path.exists(DATABASE_PATH):
        print(f"📦 Création de la base à {DATABASE_PATH}")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY(ticket_id) REFERENCES tickets(id)
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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, status, action, created_at, resolved FROM tickets")
    tickets = []
    for row in cursor.fetchall():
        ticket = {
            "id": row[0],
            "name": row[1],
            "status": row[2],
            "action": row[3],
            "created_at": row[4],
            "resolved": bool(row[5]),
            "comments": []
        }
        cursor.execute("SELECT id, text, date FROM comments WHERE ticket_id = ?", (row[0],))
        ticket["comments"] = [{"id": c[0], "text": c[1], "date": c[2]} for c in cursor.fetchall()]
        tickets.append(ticket)

    conn.close()
    return jsonify(tickets)

@app.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.json
    if not data or not all(k in data for k in ("name", "status", "action")):
        return jsonify({"error": "Données manquantes"}), 400

    created_at = datetime.now().isoformat()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tickets (name, status, action, created_at)
        VALUES (?, ?, ?, ?)
    """, (data["name"], data["status"], data["action"], created_at))
    conn.commit()
    conn.close()
    return jsonify({"message": "Ticket créé"}), 201

@app.route("/tickets/<int:ticket_id>", methods=["PUT"])
def resolve_ticket(ticket_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET resolved = NOT resolved WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Ticket mis à jour"}), 200

@app.route("/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE ticket_id = ?", (ticket_id,))
    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Ticket supprimé"}), 200

@app.route("/tickets/<int:ticket_id>/comment", methods=["POST"])
def add_comment(ticket_id):
    data = request.json
    print("📝 Données reçues :", data)
    if not data or "text" not in data:
        return jsonify({"error": "Texte manquant"}), 400

    now = datetime.now().isoformat()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO comments (ticket_id, text, date) VALUES (?, ?, ?)", (ticket_id, data["text"], now))
    conn.commit()
    conn.close()
    return jsonify({"message": "Commentaire ajouté"}), 201

@app.route("/tickets/<int:ticket_id>/comment/<int:comment_id>", methods=["DELETE"])
def delete_comment(ticket_id, comment_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE id = ? AND ticket_id = ?", (comment_id, ticket_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Commentaire supprimé"}), 200

# ✅ Route temporaire d'upload de la base
@app.route("/upload-db", methods=["GET", "POST"])
def upload_db():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename.endswith(".db"):
            return "❌ Fichier invalide. Envoyez un fichier .db"
        
        target_folder = "/opt/render/project/persistent"
        os.makedirs(target_folder, exist_ok=True)
        save_path = os.path.join(target_folder, "database.db")

        try:
            file.save(save_path)
            return f"✅ Base enregistrée avec succès à {save_path}"
        except Exception as e:
            return f"❌ Erreur lors de l'enregistrement : {e}"

    return '''
    <h2>Uploader votre base SQLite (.db)</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" accept=".db">
        <button type="submit">Envoyer</button>
    </form>
    '''

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)