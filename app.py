from flask import Flask, render_template, request, jsonify
from datetime import datetime 
import json
import os

app = Flask(__name__)

# Fichier JSON pour stocker les tickets
TICKET_FILE = "tickets.json"

# Vérifie si le fichier JSON existe, sinon crée un fichier vide
if not os.path.exists(TICKET_FILE):
    with open(TICKET_FILE, "w") as f:
        json.dump([], f)

# Charger les tickets
def load_tickets():
    with open(TICKET_FILE, "r") as f:
        tickets = json.load(f)
        for ticket in tickets:
            if "comments" not in ticket:
                ticket["comments"] = []  # Ajoute une liste vide si elle n'existe pas
        return tickets

# Sauvegarder les tickets
def save_tickets(tickets):
    with open(TICKET_FILE, "w") as f:
        json.dump(tickets, f, indent=4)

# Route principale (affiche la page web)
@app.route("/")
def home():
    return render_template("index.html")

# API pour récupérer les tickets
@app.route("/tickets", methods=["GET"])
def get_tickets():
    return jsonify(load_tickets())

# API pour ajouter un ticket
@app.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.json
    tickets = load_tickets()
    new_ticket = {
        "id": len(tickets) + 1,
        "name": data["name"],
        "status": data["status"],
        "action": data["action"],
        "created_at": datetime.now().strftime("%Y.%m.%d"),
        "resolved": False,
        "comments": []
    }
    tickets.append(new_ticket)
    save_tickets(tickets)
    return jsonify(new_ticket), 201

# API pour ajouter un commentaire a un ticket
@app.route("/tickets/<int:ticket_id>/comment", methods=["POST"])
def add_comment(ticket_id):
    data = request.json
    tickets = load_tickets()
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["comments"].append({"text": data["comment"], "date": datetime.now().strftime("%Y.%m.%d")})
            save_tickets(tickets)
            return jsonify({"message": "Commentaire ajouté"}), 201
    return jsonify({"error": "Ticket introuvable"}), 404

# API pour supprimer un commentaire a un ticket
@app.route("/tickets/<int:ticket_id>/comment/<int:comment_index>", methods=["DELETE"])
def delete_comment(ticket_id, comment_index):
    tickets = load_tickets()
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            if 0 <= comment_index < len(ticket["comments"]):
                del ticket["comments"][comment_index]
                save_tickets(tickets)
                return jsonify({"message": "Commentaire supprimé"}), 200
            return jsonify({"error": "Commentaire introuvable"}), 404
    return jsonify({"error": "Ticket introuvable"}), 404

# API pour marquer un ticket comme résolu
@app.route("/tickets/<int:ticket_id>", methods=["PUT"])
def resolve_ticket(ticket_id):
    tickets = load_tickets()
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["resolved"] = not ticket["resolved"]
            save_tickets(tickets)
            return jsonify(ticket)
    return jsonify({"error": "Ticket not found"}), 404

# API pour supprimer un ticket
@app.route("/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    tickets = load_tickets()
    tickets = [ticket for ticket in tickets if ticket["id"] != ticket_id]
    save_tickets(tickets)
    return jsonify({"message": "Ticket supprimé"}), 200

if __name__ == "__main__":
    app.run(debug=True)
