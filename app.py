# ============================================================
# Application de consultation des notes des étudiants
# ============================================================
import os
import sqlite3
import auth
from flask import Flask, jsonify, request

app = Flask(__name__)

# Fichier où sont conservées les notes de l'école
DB = "notes.db"


# Prépare le registre des notes au démarrage de l'application
def init_db():
    with sqlite3.connect(DB) as con:
        # Chaque note concerne un étudiant, dans un module
        con.execute(
            "CREATE TABLE IF NOT EXISTS notes "
            "(id INTEGER PRIMARY KEY, etudiant TEXT, module TEXT, note REAL)"
        )
        # Si le registre est vide, on y inscrit deux notes d'exemple
        if con.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
            con.executemany(
                "INSERT INTO notes (etudiant, module, note) VALUES (?, ?, ?)",
                [("Amina", "DevSecOps", 15.5), ("Youssef", "DevSecOps", 12.0)],
            )


init_db()


# Page d'accueil : l'étudiant y trouve le lien vers les notes
@app.route("/")
def accueil():
    return (
        "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
        "<title>Notes des etudiants</title></head><body>"
        "<h1>Consultation des notes</h1>"
        "<p><a href='/notes'>Voir les notes</a></p></body></html>"
    )


# Indique que le service des notes est disponible
@app.route("/health")
def health():
    return jsonify(status="ok", version="1.0")


# Consultation des notes : toutes les notes,
# ou seulement celles d'un étudiant si on donne son nom
# Exemple : /notes?etudiant=Amina
@app.route("/notes")
def lister_notes():
    # Nom de l'étudiant recherché (facultatif)
    etudiant = request.args.get("etudiant", "")
    with sqlite3.connect(DB) as con:
        rows = con.execute(
            "SELECT id, etudiant, module, note FROM notes WHERE etudiant LIKE ?",
            (f"%{etudiant}%",),
        ).fetchall()
    # Pour chaque note : l'étudiant, le module et la note obtenue
    return jsonify(
        [{"id": r[0], "etudiant": r[1], "module": r[2], "note": r[3]} for r in rows]
    )

# Modification d'une note avec contrôle des autorisations
@app.route("/notes/<int:note_id>", methods=["PUT"])
def modifier_note(note_id):
    try:
        # S2 : vérifier l'identification
        utilisateur = auth.utilisateur_connecte()
        if utilisateur is None:
            return jsonify(erreur="Authentification requise"), 401

        # S3 : seul un enseignant peut modifier une note
        if utilisateur.get("role") != "enseignant":
            return jsonify(erreur="Accès interdit"), 403

        # S5 : vérifier la validité de la note
        donnees = request.get_json(silent=True) or {}
        note = donnees.get("note")

        if isinstance(note, bool) or not isinstance(note, (int, float)):
            return jsonify(erreur="Note invalide"), 400

        if not 0 <= note <= 20:
            return jsonify(erreur="Note invalide"), 400

        with sqlite3.connect(DB) as con:
            # S4 : vérifier le module de l'enseignant
            resultat = con.execute(
                "SELECT module FROM notes WHERE id = ?", (note_id,)
            ).fetchone()

            if resultat is None:
                return jsonify(erreur="Note introuvable"), 404

            if resultat[0] != utilisateur.get("module"):
                return jsonify(erreur="Accès interdit"), 403

            # S6 : modifier la note autorisée
            con.execute(
                "UPDATE notes SET note = ? WHERE id = ?",
                (note, note_id),
            )

        return jsonify(message="Note modifiée"), 200

    except sqlite3.Error:
        # S7 : ne pas afficher les détails techniques
        return jsonify(erreur="Erreur interne"), 500
# Démarrage du service des notes, sur ce poste uniquement
if __name__ == "__main__":
    app.run(host=os.environ.get("APP_HOST", "127.0.0.1"), port=5000)
