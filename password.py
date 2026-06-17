import os, json, sys, gc, secrets, time, re, string, webbrowser, tkinter as tk, hashlib, subprocess, random
from tkinter import messagebox
import pyautogui
import pyperclip
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import nacl.pwhash
from nacl.secret import SecretBox

pyautogui.FAILSAFE = False

if sys.gettrace() is not None:
    sys.exit()

if os.name == 'nt':
    DATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'VilksPass')
else:
    DATA_DIR = os.path.expanduser('~/.vilkspass')

os.makedirs(DATA_DIR, exist_ok=True)

DB_FILE        = os.path.join(DATA_DIR, "passwords.vilks")
SESSION_FILE   = os.path.join(DATA_DIR, "session.vilks")

MAX_TENTATIVES = 5
DELAI_LOCK_SEC = 30
TIMEOUT_IDLE   = 300 
ARGON2_OPS     = 4
ARGON2_MEM     = 512 * 1024 * 1024 
SALT_SIZE      = 16
APP_PEPPER     = b"VilksPass::Pepper::v1"

BG      = "#1e1e26"
PANEL   = "#252530"
CARD    = "#2d2d3a"
INPUT   = "#38384a"
BORDER  = "#4a4a6a"
ACCENT  = "#5c6bc0"
ACCENT2 = "#7986cb"
GREEN   = "#66bb6a"
RED     = "#e57373"
TEXT    = "#e0e0e0"
MUTED   = "#9090a0"
WHITE   = "#ffffff"
F       = "Segoe UI"

def get_hwid():
    try:
        if os.name == 'nt':
            cmd = 'powershell -NoProfile -Command "(Get-CimInstance Win32_ComputerSystemProduct).UUID"'
        else:
            cmd = "cat /etc/machine-id"
        
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        hwid = subprocess.check_output(cmd, shell=True, startupinfo=startupinfo).decode().strip()
        if not hwid or "Erreur" in hwid:
            return "fallback_hwid_device_v1"
        return hwid
    except:
        return "fallback_hwid_device_v1"

def burn(v):
    if isinstance(v, bytearray):
        for i in range(len(v)): v[i] = 0
    del v; gc.collect()

def generer_mot_de_passe(n=20):
    if n < 12: n = 12
    alpha = string.ascii_letters + string.digits + "!@#$%^&*_+-=[]{}|;:,.<>?"
    pool = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*_+-=[]{}|;:,.<>?"),
    ] + [secrets.choice(alpha) for _ in range(n - 4)]
    for i in range(len(pool)-1, 0, -1):
        j = secrets.randbelow(i+1); pool[i], pool[j] = pool[j], pool[i]
    return "".join(pool)

def deriver_cles(username, password, salt):
    nom = username.lower().strip()
    secret = APP_PEPPER + nom.encode() + b":" + password.encode()
    composite = nacl.pwhash.argon2id.kdf(
        size=64, password=secret, salt=salt,
        opslimit=ARGON2_OPS, memlimit=ARGON2_MEM,
    )
    a, b = composite[:32], composite[32:]
    burn(bytearray(composite))
    return a, b

def lire_base(username, password):
    if sys.gettrace() is not None: sys.exit()
    if not os.path.exists(DB_FILE): return None, None, None
    try:
        with open(DB_FILE, "rb") as fh: raw = fh.read()
        if len(raw) < SALT_SIZE + 12 + 1: return None, None, None
        salt      = raw[:SALT_SIZE]
        nonce_aes = raw[SALT_SIZE:SALT_SIZE+12]
        chiffre   = raw[SALT_SIZE+12:]
        ca, cc = deriver_cles(username, password, salt)
        box    = SecretBox(cc)
        e1     = box.decrypt(chiffre)
        json_b = AESGCM(ca).decrypt(nonce_aes, e1, None)
        paquet = json.loads(json_b.decode())
        
        meta = paquet.get("__meta__", {})
        sign_stockee = meta.get("sign")
        
        paquet_verif = {k: v for k, v in paquet.items()}
        paquet_verif["__meta__"] = {k: v for k, v in meta.items() if k != "sign"}
        
        sign_calculee = hashlib.sha256(json.dumps(paquet_verif, sort_keys=True).encode() + ca).hexdigest()
        
        if sign_stockee and sign_calculee != sign_stockee: 
            return None, None, None
            
        burn(bytearray(e1)); burn(bytearray(json_b))
        return paquet, ca, cc
    except Exception:
        faux_paquet = {
            "Message_De_Vilks": {
                "user": "Salut, c'est vilks !",
                "pw": "Je ne pense pas que ce soit bien de vouloir decrypte les mdp des gens...",
                "url": "https://github.com/Vilks-Dev/VilksPass"
            },
            "Securite": {
                "user": "Par contre...",
                "pw": "Tu peux crypte les tiens la bas : https://github.com/Vilks-Dev/VilksPass",
                "url": "https://github.com/Vilks-Dev/VilksPass"
            }
        }
        return faux_paquet, None, None

def sauvegarder_base(ca, cc, paquet, salt=None):
    if sys.gettrace() is not None: sys.exit()
    if salt is None:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as fh: salt = fh.read(SALT_SIZE)
        else: salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(12)
    
    if "__meta__" not in paquet:
        paquet["__meta__"] = {}
        
    if "sign" in paquet["__meta__"]:
        del paquet["__meta__"]["sign"]
        
    paquet["__meta__"]["sign"] = hashlib.sha256(json.dumps(paquet, sort_keys=True).encode() + ca).hexdigest()
    
    j    = json.dumps(paquet, sort_keys=True).encode()
    e1   = AESGCM(ca).encrypt(nonce, j, None)
    fin  = SecretBox(cc).encrypt(e1)
    tmp  = DB_FILE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(salt); fh.write(nonce); fh.write(fin)
    os.replace(tmp, DB_FILE)
    burn(bytearray(j)); burn(bytearray(e1))

def valider_mdp(p):
    errs = []
    if len(p) < 12: errs.append("12 caracteres min")
    if not re.search(r"[A-Z]", p): errs.append("1 majuscule")
    if not re.search(r"[a-z]", p): errs.append("1 minuscule")
    if not re.search(r"[0-9]", p): errs.append("1 chiffre")
    if not re.search(r"[!@#$%^&*_+\-=\[\]{}|;:,.<>?]", p): errs.append("1 caractere special")
    return errs

def creer_session_locale(username, ca, cc):
    try:
        cle_session = hashlib.sha256(get_hwid().encode() + b"::VilksSessionKey").digest()
        donnees_session = {
            "username": username,
            "ca": ca.hex(),
            "cc": cc.hex(),
            "expires": time.time() + (3600 * 24 * 30)
        }
        nonce = os.urandom(12)
        chiffre = AESGCM(cle_session).encrypt(nonce, json.dumps(donnees_session).encode(), None)
        with open(SESSION_FILE, "wb") as f:
            f.write(nonce + chiffre)
    except:
        pass

def charger_session_locale():
    if not os.path.exists(SESSION_FILE) or not os.path.exists(DB_FILE):
        return None
    try:
        cle_session = hashlib.sha256(get_hwid().encode() + b"::VilksSessionKey").digest()
        with open(SESSION_FILE, "rb") as f:
            raw = f.read()
        if len(raw) < 13: return None
        nonce = raw[:12]
        chiffre = raw[12:]
        json_b = AESGCM(cle_session).decrypt(nonce, chiffre, None)
        donnees = json.loads(json_b.decode())
        
        if time.time() > donnees.get("expires", 0):
            supprimer_session_locale()
            return None
            
        ca = bytes.fromhex(donnees["ca"])
        cc = bytes.fromhex(donnees["cc"])
        username = donnees["username"]
        
        with open(DB_FILE, "rb") as fh: raw_db = fh.read()
        salt = raw_db[:SALT_SIZE]
        nonce_aes = raw_db[SALT_SIZE:SALT_SIZE+12]
        chiffre_db = raw_db[SALT_SIZE+12:]
        e1 = SecretBox(cc).decrypt(chiffre_db)
        json_db = AESGCM(ca).decrypt(nonce_aes, e1, None)
        paquet = json.loads(json_db.decode())
        
        return paquet, ca, cc, username
    except:
        supprimer_session_locale()
        return None

def supprimer_session_locale():
    if os.path.exists(SESSION_FILE):
        try: os.remove(SESSION_FILE)
        except: pass

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("VilksPass")
        self.root.geometry("1060x660")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.ca = self.cc = self.salt = self.username = None
        self.data = {}
        self.svc  = None
        self._tries = 0
        self._lock  = 0.0
        
        self.last_activity = time.time()
        self.root.bind_all("<Key>", self._reset_timer)
        self.root.bind_all("<Button-1>", self._reset_timer)
        self._check_idle()
        
        session_auto = charger_session_locale()
        if session_auto:
            paquet, ca, cc, username = session_auto
            self.username = username
            self.ca = ca
            self.cc = cc
            self.data = {k:v for k,v in paquet.items() if k != "__meta__"}
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "rb") as fh: self.salt = fh.read(SALT_SIZE)
            self._pg_main()
        elif not os.path.exists(DB_FILE): 
            self._pg_creation()
        else:                           
            self._pg_login()

    def _reset_timer(self, event=None):
        self.last_activity = time.time()

    def _check_idle(self):
        if self.ca and (time.time() - self.last_activity > TIMEOUT_IDLE):
            self._wipe()
            self._pg_login()
        self.root.after(5000, self._check_idle)

    def _clear(self):
        for w in self.root.winfo_children(): w.destroy()

    def _entry(self, parent, show="", w=36):
        e = tk.Entry(parent, show=show, font=(F,11), bg=INPUT, fg=TEXT,
                     insertbackground=TEXT, relief="flat", bd=10,
                     highlightthickness=0, width=w)
        return e

    def _btn(self, parent, text, cmd, bg=ACCENT, fg=WHITE, size=10, pad=(14,9)):
        return tk.Button(parent, text=text, command=cmd,
                         font=(F, size, "bold"), bg=bg, fg=WHITE,
                         relief="flat", bd=0, cursor="hand2",
                         activebackground=ACCENT2, activeforeground=WHITE,
                         padx=pad[0], pady=pad[1])

    def _label(self, parent, text, size=10, bold=False, color=TEXT, **kw):
        return tk.Label(parent, text=text,
                        font=(F, size, "bold" if bold else "normal"),
                        bg=parent.cget("bg"), fg=color, **kw)

    def _split_layout(self):
        left = tk.Frame(self.root, bg=BG, width=400)
        left.pack(side="left", fill="y"); left.pack_propagate(False)
        right = tk.Frame(self.root, bg=CARD)
        right.pack(side="right", fill="both", expand=True)
        return left, right

    def _pg_creation(self):
        self._clear()
        left, right = self._split_layout()
        tk.Frame(left, bg=BG).pack(expand=True)
        inner = tk.Frame(left, bg=BG, padx=48); inner.pack(fill="x")
        self._label(inner, "V", 52, bold=True, color=ACCENT).pack(anchor="w")
        self._label(inner, "VilksPass", 22, bold=True).pack(anchor="w", pady=(0,4))
        self._label(inner, "Gestionnaire de mots de passe\nchiffre et securise.", 11, color=MUTED, justify="left").pack(anchor="w")
        tk.Frame(left, bg=BG).pack(expand=True)
        form = tk.Frame(right, bg=CARD, padx=52, pady=0); form.pack(fill="both", expand=True)
        tk.Frame(form, bg=CARD).pack(expand=True)
        inner_form = tk.Frame(form, bg=CARD); inner_form.pack(fill="x")
        self._label(inner_form, "Creer votre coffre", 20, bold=True).pack(anchor="w", pady=(0,6))
        self._label(inner_form, "Choisissez des identifiants forts.", 9, color=MUTED).pack(anchor="w", pady=(0,28))
        self._label(inner_form, "NOM D'UTILISATEUR", 8, color=MUTED).pack(anchor="w")
        e_user = self._entry(inner_form, w=38); e_user.pack(fill="x", pady=(4,18)); e_user.focus()
        self._label(inner_form, "MOT DE PASSE MAITRE", 8, color=MUTED).pack(anchor="w")
        e_pwd = self._entry(inner_form, show="*", w=38); e_pwd.pack(fill="x", pady=(4,4))
        self._label(inner_form, "CONFIRMER", 8, color=MUTED).pack(anchor="w", pady=(10,0))
        e_conf = self._entry(inner_form, show="*", w=38); e_conf.pack(fill="x", pady=(4,4))
        lbl_err = tk.Label(inner_form, text="", font=(F,9), bg=CARD, fg=RED); lbl_err.pack(anchor="w", pady=(6,0))
        
        def creer():
            u=e_user.get().strip(); p=e_pwd.get(); pc=e_conf.get()
            if not u or not p or not pc: lbl_err.config(text="Tous les champs sont requis."); return
            if p != pc: lbl_err.config(text="Les mots de passe ne correspondent pas."); return
            errs = valider_mdp(p)
            if errs: lbl_err.config(text="Criteres non respectes : " + ", ".join(errs)); return
            lbl_err.config(text="Creation en cours...", fg=MUTED); self.root.update()
            self.username = u
            self.salt = os.urandom(SALT_SIZE); ca, cc = deriver_cles(u, p, self.salt)
            paquet = {"__meta__": {"username": u}}
            sauvegarder_base(ca, cc, paquet, self.salt); self.data = {}; self.ca = ca; self.cc = cc
            messagebox.showinfo("Coffre cree", "Succes !")
            self._pg_main()
        self._btn(inner_form, "Creer mon coffre", creer, size=11, pad=(20,12)).pack(fill="x", pady=(16,0))
        tk.Frame(form, bg=CARD).pack(expand=True)

    def _pg_login(self):
        self._clear()
        left, right = self._split_layout()
        tk.Frame(left, bg=BG).pack(expand=True)
        inner = tk.Frame(left, bg=BG, padx=48); inner.pack(fill="x")
        self._label(inner, "V", 52, bold=True, color=ACCENT).pack(anchor="w")
        self._label(inner, "VilksPass", 22, bold=True).pack(anchor="w", pady=(0,4))
        tk.Frame(left, bg=BG).pack(expand=True)
        form = tk.Frame(right, bg=CARD, padx=52); form.pack(fill="both", expand=True)
        tk.Frame(form, bg=CARD).pack(expand=True)
        inner_form = tk.Frame(form, bg=CARD); inner_form.pack(fill="x")
        self._label(inner_form, "Connexion", 20, bold=True).pack(anchor="w", pady=(0,6))
        self._label(inner_form, "NOM D'UTILISATEUR", 8, color=MUTED).pack(anchor="w")
        self._eu = self._entry(inner_form, w=38); self._eu.pack(fill="x", pady=(4,18)); self._eu.focus()
        self._label(inner_form, "MOT DE PASSE MAITRE", 8, color=MUTED).pack(anchor="w")
        self._ep = self._entry(inner_form, show="*", w=38); self._ep.pack(fill="x", pady=(4,6))
        
        self.var_rester = tk.BooleanVar(value=False)
        chk_rester = tk.Checkbutton(inner_form, text="Rester connecté sur cet ordinateur", variable=self.var_rester, 
                                    bg=CARD, fg=TEXT, selectcolor=INPUT, font=(F, 9),
                                    activebackground=CARD, activeforeground=TEXT, relief="flat", bd=0)
        chk_rester.pack(anchor="w", pady=(4,0))

        self._lbl_err = tk.Label(inner_form, text="", font=(F,9), bg=CARD, fg=RED); self._lbl_err.pack(anchor="w", pady=(6,0))
        self._btn(inner_form, "Deverrouiller", self._login, size=11, pad=(20,12)).pack(fill="x", pady=(16,0))
        self._ep.bind("<Return>", lambda _: self._login())
        tk.Frame(form, bg=CARD).pack(expand=True)

    def _login(self):
        restant = self._lock - time.time()
        if restant > 0: self._lbl_err.config(text=f"Verrouille — reessayez dans {int(restant)+1}s"); return
        u = self._eu.get().strip(); mp = self._ep.get()
        if not u or not mp: self._lbl_err.config(text="Champs incomplets."); return
        self._lbl_err.config(text="Verification...", fg=MUTED); self.root.update()
        res, ca, cc = lire_base(u, mp)
        if res is None:
            self._tries += 1
            left = MAX_TENTATIVES - self._tries
            if left <= 0: self._lock = time.time() + DELAI_LOCK_SEC; self._tries = 0; self._lbl_err.config(text=f"Verrouille {DELAI_LOCK_SEC}s.", fg=RED)
            else: self._lbl_err.config(text=f"Identifiants incorrects. ({left} essai(s))", fg=RED)
            return
            
        if self.var_rester.get():
            creer_session_locale(u, ca, cc)
        else:
            supprimer_session_locale()

        self.username = u
        self._tries = 0; self._lock = 0.0; self.data = {k:v for k,v in res.items() if k != "__meta__"}; self.ca = ca; self.cc = cc
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as fh: self.salt = fh.read(SALT_SIZE)
        self._pg_main()

    def _pg_main(self):
        self._clear()
        sidebar = tk.Frame(self.root, bg=PANEL, width=260)
        sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)
        hdr = tk.Frame(sidebar, bg=PANEL, padx=20, pady=22); hdr.pack(fill="x")
        self._label(hdr, "VilksPass", 15, bold=True, color=ACCENT).pack(anchor="w")
        self._label(hdr, "Coffre personnel", 9, color=MUTED).pack(anchor="w")
        srch_wrap = tk.Frame(sidebar, bg=INPUT, padx=12, pady=0); srch_wrap.pack(fill="x", padx=16, pady=14)
        self._vsrch = tk.StringVar(); e_srch = tk.Entry(srch_wrap, textvariable=self._vsrch, font=(F,10), bg=INPUT, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0)
        e_srch.pack(fill="x", pady=8); self._vsrch.trace_add("write", lambda *_: self._refresh_list())
        list_wrap = tk.Frame(sidebar, bg=PANEL); list_wrap.pack(fill="both", expand=True)
        self._lb = tk.Listbox(list_wrap, font=(F,10), bd=0, bg=PANEL, fg=TEXT, selectbackground=ACCENT, selectforeground=WHITE, highlightthickness=0, activestyle="none", cursor="hand2")
        self._lb.pack(fill="both", expand=True, padx=0, pady=8); self._lb.bind("<<ListboxSelect>>", self._load_svc)
        ftr = tk.Frame(sidebar, bg=PANEL, padx=16, pady=16); ftr.pack(fill="x")
        self._btn(ftr, "+ Nouveau compte", lambda: self._interface_edition(None), size=10, pad=(12,10)).pack(fill="x", pady=(0,8))
        self._btn(ftr, "Deconnexion", lambda: [self._wipe(), supprimer_session_locale(), self._pg_login()], bg=INPUT, fg=MUTED, size=9, pad=(12,8)).pack(fill="x")
        self._panel = tk.Frame(self.root, bg=BG); self._panel.pack(side="right", fill="both", expand=True)
        self._refresh_list(); self._empty_panel()

    def _wipe(self):
        if self.ca: burn(bytearray(self.ca))
        if self.cc: burn(bytearray(self.cc))
        self.ca = self.cc = None; self.data = {}; self.svc = None

    def _empty_panel(self):
        for w in self._panel.winfo_children(): w.destroy()
        f = tk.Frame(self._panel, bg=BG); f.place(relx=0.5, rely=0.5, anchor="center")
        self._label(f, "Selectionnez un compte", 13, color=MUTED).pack()

    def _refresh_list(self, *_):
        filtre = self._vsrch.get().lower(); self._lb.delete(0, tk.END)
        for svc in sorted(self.data.keys()):
            if filtre in svc.lower(): self._lb.insert(tk.END, f"  {svc}")

    def _paste_text(self, text):
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        self.root.after(500, lambda: pyperclip.copy(""))

    @staticmethod
    def _normaliser_url(url):
        if not url:
            return url
        url = url.strip()
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://', url):
            url = "https://" + url
        return url

    @staticmethod
    def _detecter_navigateur_ouvert():
        if os.name != 'nt':
            return None, None
        navigateurs = [
            ("chrome",  "chrome.exe"),
            ("msedge",  "msedge.exe"),
            ("firefox", "firefox.exe"),
            ("brave",   "brave.exe"),
            ("opera",   "opera.exe"),
        ]
        try:
            sortie = subprocess.check_output(
                ["tasklist", "/fo", "csv", "/nh"],
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode(errors="replace").lower()
            for nom, exe in navigateurs:
                if exe in sortie:
                    return nom, exe
        except Exception:
            pass
        return None, None

    @staticmethod
    def _chemin_exe_navigateur(nom):
        chemins = {
            "chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ],
            "msedge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ],
            "firefox": [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ],
            "brave": [
                os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            ],
            "opera": [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera\launcher.exe"),
            ],
        }
        for chemin in chemins.get(nom, []):
            if os.path.exists(chemin):
                return chemin
        return None

    def _ouvrir_url_intelligemment(self, url):
        url = self._normaliser_url(url)
        if not url:
            return
        nom, _ = self._detecter_navigateur_ouvert()
        chemin = self._chemin_exe_navigateur(nom) if nom else None
        if chemin:
            try:
                flag = "--new-tab" if nom != "firefox" else "-new-tab"
                subprocess.Popen(
                    [chemin, flag, url],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return
            except Exception:
                pass
        webbrowser.open(url)

    def _auto_fill(self, user, pwd, url):
        for w in self._panel.winfo_children(): w.destroy()
        wrap = tk.Frame(self._panel, bg=BG); wrap.pack(expand=True, fill="both")

        lbl_msg = tk.Label(wrap, text="", font=(F, 14, "bold"), bg=BG, fg=WHITE)
        lbl_msg.place(relx=0.5, rely=0.35, anchor="center")
        lbl_timer = tk.Label(wrap, text="", font=(F, 48, "bold"), bg=BG, fg=WHITE)
        lbl_timer.place(relx=0.5, rely=0.55, anchor="center")

        url_normalisee = self._normaliser_url(url) if url else None

        def phase1_ouvrir():
            if url_normalisee:
                lbl_msg.config(text="Ouverture du site...", fg=MUTED)
                self.root.update()
                self._ouvrir_url_intelligemment(url_normalisee)
                self.root.after(2000, phase2_attente_utilisateur)
            else:
                phase2_attente_utilisateur()

        def phase2_attente_utilisateur():
            lbl_msg.config(
                text="Cliquez dans le champ IDENTIFIANT puis MOT DE PASSE !",
                fg=GREEN
            )
            lbl_timer.config(text="5")
            self.root.update()
            decompte(5)

        def decompte(n):
            if n > 0:
                lbl_timer.config(text=str(n))
                self.root.update()
                self.root.after(1000, lambda: decompte(n - 1))
            else:
                phase3_ecrire()

        def phase3_ecrire():
            lbl_msg.config(text="Écriture en cours...", fg=ACCENT)
            lbl_timer.config(text="")
            self.root.update()

            self._paste_text(user)
            pyautogui.press("tab")
            time.sleep(0.3)
            self._paste_text(pwd)
            pyautogui.press("enter")

            self.root.after(1000, self._load_svc)

        self.root.after(100, phase1_ouvrir)

    def _load_svc(self, _=None):
        sel = self._lb.curselection()
        if sel: self.svc = self._lb.get(sel[0]).strip()
        if not self.svc or self.svc not in self.data: return
        info = self.data[self.svc]
        for w in self._panel.winfo_children(): w.destroy()
        wrap = tk.Frame(self._panel, bg=BG, padx=40, pady=36); wrap.pack(fill="both", expand=True)
        self._label(wrap, self.svc, 24, bold=True).pack(anchor="w")
        def row(parent, titre_row, valeur, secret=False):
            self._label(parent, titre_row, 8, color=MUTED).pack(anchor="w", pady=(15,0))
            r = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1); r.pack(fill="x", pady=(4,0))
            if not secret:
                tk.Label(r, text=valeur, font=(F,11), bg=CARD, fg=TEXT, anchor="w").pack(side="left", padx=16, pady=12, expand=True, fill="x")
                self._btn(r, "Copier", lambda v=valeur: self._copy(v), bg=INPUT, fg=MUTED, size=9, pad=(12,8)).pack(side="right", padx=8, pady=8)
            else:
                visible = tk.BooleanVar(value=False); lv = tk.Label(r, text="* * * * * * * * * *", font=(F,11), bg=CARD, fg=MUTED, anchor="w"); lv.pack(side="left", padx=16, pady=12, expand=True, fill="x")
                def tog():
                    visible.set(not visible.get()); lv.config(text=valeur if visible.get() else "* * * * * * * * * *", fg=TEXT if visible.get() else MUTED)
                    btn_eye.config(text="Masquer" if visible.get() else "Afficher")
                btn_eye = self._btn(r, "Afficher", tog, bg=INPUT, fg=MUTED, size=9, pad=(12,8)); btn_eye.pack(side="right", padx=4, pady=8)
                self._btn(r, "Copier", lambda v=valeur: self._copy(v), bg=INPUT, fg=MUTED, size=9, pad=(12,8)).pack(side="right", padx=0, pady=8)
        row(wrap, "IDENTIFIANT", info["user"]); row(wrap, "MOT DE PASSE", info["pw"], secret=True)
        if info.get("url"): row(wrap, "URL", info["url"])
        acts = tk.Frame(wrap, bg=BG); acts.pack(fill="x", pady=30)
        self._btn(acts, "Auto-Remplir", lambda: self._auto_fill(info["user"], info["pw"], info.get("url")), bg=GREEN, size=10, pad=(16,11)).pack(side="left", padx=(0,10))
        self._btn(acts, "Modifier", lambda: self._interface_edition(self.svc), bg=INPUT, fg=MUTED, size=10, pad=(16,11)).pack(side="left")
        self._btn(acts, "Supprimer", lambda: self._delete(self.svc), bg="#2a1010", fg=RED, size=10, pad=(16,11)).pack(side="left", padx=10)

    def _interface_edition(self, nom_service):
        for w in self._panel.winfo_children(): w.destroy()
        info = self.data.get(nom_service, {"user":"","pw":"","url":""})
        wrap = tk.Frame(self._panel, bg=BG, padx=40, pady=36); wrap.pack(fill="both", expand=True)
        self._label(wrap, "Edition" if nom_service else "Nouveau", 20, bold=True).pack(anchor="w", pady=(0,20))
        def champ(parent, titre, val):
            self._label(parent, titre, 8, color=MUTED).pack(anchor="w")
            e = self._entry(parent, w=36); e.insert(0, val); e.pack(fill="x", pady=(4,16))
            return e
        e_srv = champ(wrap, "SERVICE", nom_service if nom_service else ""); e_usr = champ(wrap, "IDENTIFIANT", info["user"])
        pw_f = tk.Frame(wrap, bg=BG); pw_f.pack(fill="x"); self._label(pw_f, "MOT DE PASSE", 8, color=MUTED).pack(anchor="w")
        e_pwd = self._entry(pw_f, show="*", w=26); e_pwd.insert(0, info["pw"]); e_pwd.pack(side="left", fill="x", expand=True, pady=(4,16))
        visible = tk.BooleanVar(value=False)
        def tog_pw():
            visible.set(not visible.get()); e_pwd.config(show="" if visible.get() else "*")
            btn_v.config(text="Masquer" if visible.get() else "Afficher")
        btn_v = self._btn(pw_f, "Afficher", tog_pw, bg=INPUT, fg=MUTED, size=9, pad=(12,8)); btn_v.pack(side="right", padx=(8,0), pady=(0,12))
        self._btn(pw_f, "Generer", lambda: [e_pwd.delete(0,tk.END), e_pwd.insert(0, generer_mot_de_passe())], bg="#854d0e", size=9, pad=(12,8)).pack(side="right", padx=(8,0), pady=(0,12))
        e_url = champ(wrap, "URL", info.get("url",""))
        def save():
            s = e_srv.get().strip(); u = e_usr.get().strip(); pw = e_pwd.get(); url = e_url.get().strip()
            if not s or not u or not pw: messagebox.showwarning("Erreur", "Champs requis."); return
            if nom_service and nom_service != s: del self.data[nom_service]
            self.data[s] = {"user":u, "pw":pw, "url":url}; self.svc = s; self._save(); self._refresh_list()
            self._load_svc()
        self._btn(wrap, "Sauvegarder", save, bg=GREEN, size=11, pad=(20,12)).pack(fill="x", pady=(20,0))

    def _copy(self, v):
        pyperclip.copy(v)
        self.root.after(30000, lambda: pyperclip.copy(""))

    def _delete(self, svc):
        if messagebox.askyesno("Confirmation", "Supprimer ?"):
            del self.data[svc]; self._save(); self._refresh_list(); self._empty_panel()

    def _save(self):
        p = dict(self.data)
        p["__meta__"] = {"username": self.username}
        sauvegarder_base(self.ca, self.cc, p, self.salt)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()