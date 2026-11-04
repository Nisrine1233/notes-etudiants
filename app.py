# ============================================================
# Application de consultation des notes des étudiants
# ============================================================
import logging
import os
import sqlite3
from flask import Flask, jsonify, request
from auth import utilisateur_connecte

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

# Modification d'une note par l'enseignant
@app.route("/notes/<int:note_id>", methods=["PUT"])
def modifier_note(note_id):
    # 1. Authentification : qui est l'utilisateur ?
    utilisateur = utilisateur_connecte()
    if utilisateur is None:
        return jsonify(erreur="Authentification requise"), 401

    # 2. Autorisation : seul un enseignant peut modifier
    if utilisateur["role"] != "enseignant":
        return jsonify(erreur="Accès interdit"), 403

    # 3. Validation : la note est un nombre entre 0 et 20
    donnees = request.get_json(silent=True) or {}
    note = donnees.get("note")
    if (isinstance(note, bool) or not isinstance(note, (int, float))
            or not 0 <= note <= 20):
        return jsonify(erreur="Note invalide (0 à 20)"), 400

    try:
        with sqlite3.connect(DB) as con:
            ligne = con.execute(
                "SELECT module FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            if ligne is None:
                return jsonify(erreur="Note introuvable"), 404
            # 4. Autorisation : seulement les notes de son module
            if ligne[0] != utilisateur["module"]:
                return jsonify(erreur="Accès interdit"), 403
            # 5. Requête paramétrée
            con.execute(
                "UPDATE notes SET note = ? WHERE id = ?", (note, note_id)
            )
        # 6. Trace : qui a modifié quoi
        logging.info("Note %s modifiée par %s", note_id, utilisateur["nom"])
        return jsonify(statut="ok")
    except sqlite3.Error:
        # 7. Aucun détail technique pour l'utilisateur
        logging.exception("Erreur lors de la modification de la note")
        return jsonify(erreur="Erreur interne"), 500
# Démarrage du service des notes, sur ce poste uniquement
if __name__ == "__main__":
    app.run(host=os.environ.get("APP_HOST", "127.0.0.1"), port=5000)
