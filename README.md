# VilksPass

Un gestionnaire de mots de passe sécurisé et léger conçu pour stocker et protéger vos identifiants localement avec des mécanismes de défense avancés.

### 🛡️ Fonctionnalités de Sécurité

* **Double chiffrement robuste :** Utilise `Argon2id` pour la dérivation de clés de haute sécurité, combiné à une double couche de protection via `AES-GCM` et `SecretBox` (NaCl).
* **Isolation des données :** Les fichiers de configuration et les bases de données (`.vilks`) sont automatiquement masqués et stockés dans le répertoire système de l'utilisateur (`AppData\Roaming` sous Windows ou `.vilkspass` sous Linux) pour éviter une visibilité directe.
* **Sécurisation de la mémoire :** Les clés de chiffrement en mémoire RAM sont écrasées avec des zéros (`burn`) et nettoyées immédiatement après chaque opération afin de contrer les attaques de type *cold boot*.
* **Session locale liée à la machine :** L'option "Rester connecté" chiffre une session locale en utilisant l'identifiant matériel unique de l'ordinateur (HWID). La session ne peut pas être copiée ou volée sur une autre machine.
* **Système de Leurre (Honeytoken) :** Si un attaquant parvient à voler le fichier de données et tente de le forcer ou de le décrypter avec un outil de brute-force, le fichier intercepte l'attaque et renvoie de fausses données d'avertissement au lieu de révéler vos vrais mots de passe.
* **Anti-Snooping & Auto-remplissage :** Utilise un système de temporisation interactif et une simulation de frappe clavier pour remplir vos identifiants en toute sécurité sans laisser les mots de passe visibles en clair dans le presse-papiers.
* **Anti-Debug :** Détection automatique et blocage immédiat du script si un outil d'analyse ou de débogage tente d'inspecter le processus en temps réel.
* **Auto-verrouillage :** Verrouillage automatique de l'interface en cas d'inactivité prolongée et blocage temporaire après plusieurs échecs de connexion.

### 🚀 Utilisation

1. **Lancement :** Exécutez le script avec Python (`python password.py`).
2. **Coffre :** Créez votre identifiant et votre mot de passe maître lors de la première utilisation.
3. **Gestion :** Ajoutez vos comptes, générez des mots de passe forts et utilisez la fonction d'auto-remplissage.

---

*Note : Vos données restent strictement locales, chiffrées sur votre disque, et ne transitent jamais par un serveur distant.*