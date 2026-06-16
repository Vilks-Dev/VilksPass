Voici un `README.md` concis pour le projet **VilksPass**.

---

# VilksPass

Un gestionnaire de mots de passe sécurisé conçu pour protéger vos identifiants localement avec des mécanismes de défense avancés.

### 🛡️ Fonctionnalités de Sécurité

* **Chiffrement robuste :** Utilise `Argon2id` pour la dérivation de clés, `AES-GCM` pour les données et `SecretBox` (NaCl) pour une double couche de protection.
* **Protection anti-capture :** Empêche les logiciels tiers (capture d'écran, enregistreurs) de visualiser la fenêtre de l'application via `SetWindowDisplayAffinity`.
* **Sécurisation mémoire :** Tente de verrouiller les clés en mémoire RAM (`VirtualLock`) et les efface automatiquement (`burn`) après usage pour contrer les attaques de type *cold boot*.
* **Intégrité :** Vérifie que le code source n'a pas été modifié (`SHA-256`) avant l'exécution.
* **Session locale sécurisée :** Les sessions persistantes sont chiffrées via les API Windows (`CryptProtectData`) pour lier la session à votre machine.
* **Auto-remplissage protégé :** Utilise un délai de sécurité avant la saisie automatique pour éviter toute interception malveillante.
* **Anti-Debug :** Détection automatique des outils de débogage pour empêcher l'analyse du processus en temps réel.
* **Auto-verrouillage :** Fermeture automatique après une période d'inactivité définie.

### 🚀 Utilisation

1. **Lancement :** Exécutez le script avec Python.
2. **Coffre :** Créez votre coffre lors de la première utilisation.
3. **Gestion :** Ajoutez, copiez ou utilisez l'auto-remplissage pour vos comptes.

---

*Note : Vos données sont chiffrées localement et ne sont jamais envoyées sur un serveur distant.*