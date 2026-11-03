# Exigences de sécurité de l'application des notes

| # | Exigence : « Le système doit… » | Vérification | Étape du SDLC | Test |
|---|---|---|---|---|
| 1 | Le système doit empêcher les injections SQL lors de la recherche d'un étudiant. | Vérifier que la recherche utilise des requêtes paramétrées. | Développement / Test | S1 |
| 2 | Le système doit refuser la modification d'une note sans authentification. | Vérifier la présence d'un jeton valide. | Développement / Test | S2 |
| 3 | Le système doit interdire aux étudiants de modifier les notes. | Vérifier le rôle de l'utilisateur. | Développement / Test | S3 |
| 4 | Le système doit interdire à un enseignant de modifier les notes d'un autre module. | Vérifier le module associé à l'enseignant. | Développement / Test | S4 |
| 5 | Le système doit accepter uniquement les notes entre 0 et 20. | Vérifier le type et la valeur de la note. | Développement / Test | S5 |
| 6 | Le système doit permettre à l'enseignant autorisé de modifier une note. | Vérifier que la modification est enregistrée. | Développement / Test | S6 |