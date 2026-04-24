# Compiler l'application en .exe

## Prérequis

```bash
pip install pyinstaller
```

UPX (optionnel, réduit la taille du .exe) : https://github.com/upx/upx/releases

---

## Structure attendue avant de compiler

```
racine_projet/
├── main.py            ← version fournie (chemins patchés)
├── launcher.py        ← fourni
├── build.spec         ← fourni
├── icone.ico          ← ton icône
├── front_end/         ← tous les templates/CSS/JS
├── _data/
│   └── goal2.json
├── core/
└── api/
```

---

## Compilation

Depuis la racine du projet :

```bash
pyinstaller build.spec
```

Le résultat se trouve dans :

```
dist/
└── ApplicationCompte/
    ├── ApplicationCompte.exe   ← double-clic pour lancer
    ├── front_end/
    ├── _data/
    └── ...
```

Pour distribuer : zippe et envoie le dossier `dist/ApplicationCompte/` entier.

---

## Ce qui se passe au lancement du .exe

1. L'utilisateur double-clique sur `ApplicationCompte.exe`
2. Flask démarre en arrière-plan sur `http://127.0.0.1:5000`
3. **L'interface s'ouvre dans le navigateur par défaut** — ajoute cette ligne dans
   `main.py` si tu veux qu'elle s'ouvre automatiquement :

```python
import webbrowser, threading

if __name__ == '__main__':
    threading.Timer(1.2, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    app.run(debug=False)
```

---

## Dépannage courant

| Problème | Cause probable | Solution |
|---|---|---|
| `ModuleNotFoundError` au démarrage | Import caché manquant | Ajouter le module dans `hiddenimports` dans `build.spec` |
| `_data/goal2.json` introuvable | Chemin relatif cassé | Vérifier que `_data` est bien dans `added_datas` du spec |
| Fenêtre console noire qui s'ouvre | `console=True` dans le spec | Mettre `console=False` |
| Antivirus bloque le .exe | Faux positif PyInstaller courant | Signer le .exe ou ajouter une exception |