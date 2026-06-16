import os, json, sys, gc, secrets, time, re, string, webbrowser, tkinter as tk, hashlib, atexit
from tkinter import messagebox
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import nacl.pwhash
from nacl.secret import SecretBox

if sys.gettrace() is not None:
    sys.exit()

def _verifier_integrite_brute():
    try:
        path = os.path.abspath(sys.argv[0])
        if path.endswith('.py') or path.endswith('.pyc'):
            return
        with open(path, "rb") as f:
            content = f.read()
        courant = hashlib.sha256(content).hexdigest()
        sig_path = path + ".sig"
        if not os.path.exists(sig_path):
            return
        with open(sig_path, "r") as f:
            attendu = f.read().strip()
        if courant != attendu:
            sys.exit()
    except:
        sys.exit()

_verifier_integrite_brute()

DB_FILE        = "passwords.vilks"
BAK_FILE       = "passwords.vilks.bak"
SESSION_FILE   = "session.vilks"
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

_GLOBAL_CA = None
_GLOBAL_CC = None

def _nettoyage_anti_cold_boot():
    global _GLOBAL_CA, _GLOBAL_CC
    try:
        if _GLOBAL_CA:
            for i in range(len(_GLOBAL_CA)): _GLOBAL_CA[i] = secrets.randbelow(256)
        if _GLOBAL_CC:
            for i in range(len(_GLOBAL_CC)): _GLOBAL_CC[i] = secrets.randbelow(256)
    except:
        pass

atexit.register(_nettoyage_anti_cold_boot)

def _charger_dll_securisee():
    if os.name != 'nt': return None, None, None
    import ctypes
    system32 = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32')
    crypt32_path = os.path.join(system32, 'crypt32.dll')
    kernel32_path = os.path.join(system32, 'kernel32.dll')
    user32_path = os.path.join(system32, 'user32.dll')
    try:
        crypt32 = ctypes.WinDLL(crypt32_path)
        kernel32 = ctypes.WinDLL(kernel32_path)
        user32 = ctypes.WinDLL(user32_path)
        return crypt32, kernel32, user32
    except:
        return None, None, None

def Activer_Anti_Capture(hwnd):
    crypt32, kernel32, user32 = _charger_dll_securisee()
    if not user32: return
    try:
        user32.SetWindowDisplayAffinity(hwnd, 0x00000003)
    except:
        pass

def Verrouiller_Memoire_Physique(data_bytes):
    crypt32, kernel32, user32 = _charger_dll_securisee()
    if not kernel32: return
    try:
        import ctypes
        buf = ctypes.create_string_buffer(bytes(data_bytes))
        kernel32.VirtualLock(buf, len(data_bytes))
    except:
        pass

def Injection_Win32_Target(hwnd, texte):
    crypt32, kernel32, user32 = _charger_dll_securisee()
    if not user32 or not hwnd: return
    try:
        WM_SETTEXT = 0x000C
        user32.SendMessageW(hwnd, WM_SETTEXT, 0, texte)
    except:
        pass

def Windows_Chiffrer(data: bytes) -> bytes:
    crypt32, kernel32, _ = _charger_dll_securisee()
    if not crypt32: return data
    import ctypes
    from ctypes import wintypes
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]
    
    DataIn = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)))
    DataOut = DATA_BLOB()
    if crypt32.CryptProtectData(ctypes.byref(DataIn), None, None, None, None, 0, ctypes.byref(DataOut)):
        res = ctypes.string_at(DataOut.pbData, DataOut.cbData)
        kernel32.LocalFree(DataOut.pbData)
        return res
    return data

def Windows_Dechiffrer(data: bytes) -> bytes:
    crypt32, kernel32, _ = _charger_dll_securisee()
    if not crypt32: return data
    import ctypes
    from ctypes import wintypes
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]
    
    DataIn = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)))
    DataOut = DATA_BLOB()
    if crypt32.CryptUnprotectData(ctypes.byref(DataIn), None, None, None, None, 0, ctypes.byref(DataOut)):
        res = ctypes.string_at(DataOut.pbData, DataOut.cbData)
        kernel32.LocalFree(DataOut.pbData)
        return res
    raise Exception()

def burn(v):
    if isinstance(v, (bytearray, bytes)):
        try:
            for i in range(len(v)): v[i] = 0
        except: pass
    elif isinstance(v, dict):
        try:
            for k in list(v.keys()):
                burn(v[k])
                v[k] = None
        except: pass
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

def generer_nonce_securise() -> bytes:
    t = int(time.time_ns()).to_bytes(8, sys.byteorder)
    r = secrets.token_bytes(4)
    return t + r

def deriver_cles(username, password, salt):
    nom = username.lower().strip()
    secret = APP_PEPPER + nom.encode() + b":" + password.encode()
    composite = nacl.pwhash.argon2id.kdf(
        size=64, password=secret, salt=salt,
        opslimit=ARGON2_OPS, memlimit=ARGON2_MEM,
    )
    a, b = bytearray(composite[:32]), bytearray(composite[32:])
    Verrouiller_Memoire_Physique(a)
    Verrouiller_Memoire_Physique(b)
    burn(bytearray(composite))
    return a, b

def lire_base_brute():
    if not os.path.exists(DB_FILE): return None
    try:
        with open(DB_FILE, "rb") as fh: return fh.read()
    except: return None

def lire_base(username, password):
    if sys.gettrace() is not None: sys.exit()
    if not os.path.exists(DB_FILE): return None, None, None
    try:
        with open(DB_FILE, "rb") as fh: raw = fh.read()
        if len(raw) < SALT_SIZE + 12 + 1: return None, None, None
        salt = raw[:SALT_SIZE]
        ca, cc = deriver_cles(username, password, salt)
        paquet = dechi_paquet(raw, ca, cc)
        return paquet, ca, cc
    except:
        return None, None, None

def dechi_paquet(raw_data, ca, cc):
    if len(raw_data) < SALT_SIZE + 12 + 1: return None
    try:
        nonce_aes = raw_data[SALT_SIZE:SALT_SIZE+12]
        chiffre   = raw_data[SALT_SIZE+12:]
        box    = SecretBox(bytes(cc))
        e1     = box.decrypt(chiffre)
        json_b = AESGCM(bytes(ca)).decrypt(nonce_aes, e1, None)
        paquet = json.loads(json_b.decode())
        burn(e1); burn(json_b)
        return paquet
    except:
        return None

def sauvegarder_base(ca, cc, paquet, salt=None):
    if sys.gettrace() is not None: sys.exit()
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as orig, open(BAK_FILE, "wb") as bak:
                bak.write(orig.read())
        except: pass

    if salt is None:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as fh: salt = fh.read(SALT_SIZE)
        else: salt = os.urandom(SALT_SIZE)
        
    nonce = generer_nonce_securise()
    j    = json.dumps(paquet, sort_keys=True).encode()
    e1   = AESGCM(bytes(ca)).encrypt(nonce, j, None)
    fin  = SecretBox(bytes(cc)).encrypt(e1)
    tmp  = DB_FILE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(salt); fh.write(nonce); fh.write(fin)
    os.replace(tmp, DB_FILE)
    burn(j); burn(e1)

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
        donnees_session = {
            "username": username,
            "ca": ca.hex(),
            "cc": cc.hex(),
            "expires": time.time() + (3600 * 24 * 30)
        }
        payload = json.dumps(donnees_session).encode()
        payload_protege = Windows_Chiffrer(payload)
        with open(SESSION_FILE, "wb") as f: f.write(payload_protege)
    except: pass

def charger_session_locale():
    if not os.path.exists(SESSION_FILE) or not os.path.exists(DB_FILE): return None
    payload = donnees = ca_hex = cc_hex = ca = cc = None
    try:
        with open(SESSION_FILE, "rb") as f: raw = f.read()
        payload = Windows_Dechiffrer(raw)
        donnees = json.loads(payload.decode())
        if time.time() > donnees.get("expires", 0):
            supprimer_session_locale()
            return None
        ca_hex = donnees["ca"]
        cc_hex = donnees["cc"]
        ca = bytearray.fromhex(ca_hex)
        cc = bytearray.fromhex(cc_hex)
        username = donnees["username"]
        
        with open(DB_FILE, "rb") as fh: raw_db = fh.read()
        paquet = dechi_paquet(raw_db, ca, cc)
        if paquet is None: raise Exception()
        return paquet, ca, cc, username
    except:
        supprimer_session_locale()
        if ca: burn(ca)
        if cc: burn(cc)
        return None
    finally:
        if donnees:
            if "ca" in donnees: donnees["ca"] = ""
            if "cc" in donnees: donnees["cc"] = ""
        burn(payload); burn(ca_hex); burn(cc_hex)

def supprimer_session_locale():
    if os.path.exists(SESSION_FILE):
        try: os.remove(SESSION_FILE)
        except: pass


class AppVault:
    def __init__(self, root, username, ca, cc):
        self.root = root
        self.username = username
        self.ca = ca
        self.cc = cc
        self._raw_encrypted_db = lire_base_brute()
        self.salt = None
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "rb") as fh: self.salt = fh.read(SALT_SIZE)
        self.svc = None
        self.last_activity = time.time()
        self.root.bind_all("<Key>", self._reset_timer)
        self.root.bind_all("<Button-1>", self._reset_timer)
        self._check_idle()
        self._pg_main()

    def _reset_timer(self, event=None):
        self.last_activity = time.time()

    def _check_idle(self):
        if time.time() - self.last_activity > TIMEOUT_IDLE:
            self._force_exit()
        self.root.after(5000, self._check_idle)

    def _force_exit(self):
        _nettoyage_anti_cold_boot()
        self.root.destroy()
        sys.exit()

    def _clear(self):
        for w in self.root.winfo_children(): w.destroy()

    def _entry(self, parent, show="", w=36):
        e = tk.Entry(parent, show=show, font=(F,11), bg=INPUT, fg=TEXT,
                     insertbackground=TEXT, relief="flat", bd=10,
                     highlightthickness=0, width=w)
        try:
            e.tk.call(e._w, "configure", "-isameffective", "0")
        except:
            pass
        return e

    def _btn(self, parent, text, cmd, bg=ACCENT, fg=WHITE, size=10, pad=(14,9)):
        return tk.Button(parent, text=text, command=cmd,
                         font=(F, size, "bold"), bg=bg, fg=fg,
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

    def _get_decrypted_data_snapshot(self):
        if not self._raw_encrypted_db or not self.ca or not self.cc: return {}
        paquet = dechi_paquet(self._raw_encrypted_db, self.ca, self.cc)
        if not paquet: return {}
        res = {k:v for k,v in paquet.items() if k != "__meta__"}
        return res

    def _pg_main(self):
        self._clear()
        sidebar = tk.Frame(self.root, bg=PANEL, width=260)
        sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)
        hdr = tk.Frame(sidebar, bg=PANEL, padx=20, pady=22); ftr = tk.Frame(sidebar, bg=PANEL, padx=16, pady=16)
        self._label(hdr, "VilksPass", 15, bold=True, color=ACCENT).pack(anchor="w")
        srch_wrap = tk.Frame(sidebar, bg=INPUT, padx=12, pady=0); srch_wrap.pack(fill="x", padx=16, pady=14)
        self._vsrch = tk.StringVar(); e_srch = tk.Entry(srch_wrap, textvariable=self._vsrch, font=(F,10), bg=INPUT, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0)
        e_srch.pack(fill="x", pady=8); self._vsrch.trace_add("write", lambda *_: self._refresh_list())
        list_wrap = tk.Frame(sidebar, bg=PANEL); list_wrap.pack(fill="both", expand=True)
        self._lb = tk.Listbox(list_wrap, font=(F,10), bd=0, bg=PANEL, fg=TEXT, selectbackground=ACCENT, selectforeground=WHITE, highlightthickness=0, activestyle="none", cursor="hand2")
        self._lb.pack(fill="both", expand=True, padx=0, pady=8); self._lb.bind("<<ListboxSelect>>", self._load_svc)
        hdr.pack(fill="x"); ftr.pack(fill="x")
        self._btn(ftr, "+ Nouveau compte", lambda: self._interface_edition(None), size=10, pad=(12,10)).pack(fill="x", pady=(0,8))
        self._btn(ftr, "Deconnexion", lambda: [supprimer_session_locale(), self._force_exit()], bg=INPUT, fg=MUTED, size=9, pad=(12,8)).pack(fill="x")
        self._panel = tk.Frame(self.root, bg=BG); self._panel.pack(side="right", fill="both", expand=True)
        self._refresh_list(); self._empty_panel()

    def _empty_panel(self):
        for w in self._panel.winfo_children(): w.destroy()
        f = tk.Frame(self._panel, bg=BG); f.place(relx=0.5, rely=0.5, anchor="center")
        self._label(f, "Selectionnez un compte", 13, color=MUTED).pack()

    def _refresh_list(self, *_):
        filtre = self._vsrch.get().lower(); self._lb.delete(0, tk.END)
        snapshot = self._get_decrypted_data_snapshot()
        for svc in sorted(snapshot.keys()):
            if filtre in svc.lower(): self._lb.insert(tk.END, f"  {svc}")
        burn(snapshot)

    def _auto_fill(self, user, pwd, url):
        for w in self._panel.winfo_children(): w.destroy()
        wrap = tk.Frame(self._panel, bg=BG)
        wrap.pack(expand=True, fill="both")
        
        lbl_msg = tk.Label(wrap, text="Cliquez dans le champ IDENTIFIANT du site !", font=(F,14,"bold"), bg=BG, fg=GREEN)
        lbl_msg.place(relx=0.5, rely=0.35, anchor="center")
        
        lbl_timer = tk.Label(wrap, text="5", font=(F,48,"bold"), bg=BG, fg=WHITE)
        lbl_timer.place(relx=0.5, rely=0.55, anchor="center")
        self.root.update()
        
        if url: 
            webbrowser.open(url)
        
        def decompte(secondes_restantes):
            if secondes_restantes > 0:
                lbl_timer.config(text=str(secondes_restantes))
                self.root.update()
                self.root.after(1000, lambda: decompte(secondes_restantes - 1))
            else:
                lbl_msg.config(text="Écriture en cours...", fg=ACCENT)
                lbl_timer.config(text="")
                self.root.update()
                
                import pyautogui
                if user:
                    pyautogui.write(user, interval=0.01)
                    pyautogui.press('tab')
                    time.sleep(0.1)
                
                pyautogui.write(pwd if pwd else "", interval=0.01)
                pyautogui.press('enter')
                
                self.root.after(400, lambda: self._load_svc())

        self.root.after(500, lambda: decompte(5))

    def _load_svc(self, _=None):
        sel = self._lb.curselection()
        if sel: self.svc = self._lb.get(sel[0]).strip()
        snapshot = self._get_decrypted_data_snapshot()
        if not self.svc or self.svc not in snapshot: burn(snapshot); return
        info = snapshot[self.svc]
        for w in self._panel.winfo_children(): w.destroy()
        wrap = tk.Frame(self._panel, bg=BG, padx=40, pady=36); wrap.pack(fill="both", expand=True)
        self._label(wrap, self.svc, 24, bold=True).pack(anchor="w")
        
        def row(parent, titre_row, valeur, secret=False):
            self._label(parent, titre_row, 8, color=MUTED).pack(anchor="w", pady=(15,0))
            r = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1); r.pack(fill="x", pady=(4,0))
            if not secret:
                tk.Label(r, text=valeur, font=(F,11), bg=CARD, fg=TEXT, anchor="w").pack(side="left", padx=16, pady=12, expand=True, fill="x")
                import pyperclip
                self._btn(r, "Copier", lambda v=valeur: [pyperclip.copy(v), self.root.after(5000, lambda: pyperclip.copy(""))], bg=INPUT, fg=MUTED, size=9, pad=(12,8)).pack(side="right", padx=8, pady=8)
            else:
                visible = tk.BooleanVar(value=False); lv = tk.Label(r, text="* * * * * * * * * *", font=(F,11), bg=CARD, fg=MUTED, anchor="w"); lv.pack(side="left", padx=16, pady=12, expand=True, fill="x")
                def tog():
                    visible.set(not visible.get()); lv.config(text=valeur if visible.get() else "* * * * * * * * * *", fg=TEXT if visible.get() else MUTED)
                    btn_eye.config(text="Masquer" if visible.get() else "Afficher")
                btn_eye = self._btn(r, "Afficher", tog, bg=INPUT, fg=MUTED, size=9, pad=(12,8)); btn_eye.pack(side="right", padx=4, pady=8)
                import pyperclip
                self._btn(r, "Copier", lambda v=valeur: [pyperclip.copy(v), self.root.after(5000, lambda: pyperclip.copy(""))], bg=INPUT, fg=MUTED, size=9, pad=(12,8)).pack(side="right", padx=0, pady=8)
                
        row(wrap, "IDENTIFIANT", info.get("user", "")); row(wrap, "MOT DE PASSE", info.get("pw", ""), secret=True)
        if info.get("url"): row(wrap, "URL", info["url"])
        acts = tk.Frame(wrap, bg=BG); acts.pack(fill="x", pady=30)
        self._btn(acts, "Auto-Remplir", lambda: self._auto_fill(info.get("user"), info.get("pw"), info.get("url")), bg=GREEN, size=10, pad=(16,11)).pack(side="left", padx=(0,10))
        self._btn(acts, "Modifier", lambda: self._interface_edition(self.svc), bg=INPUT, fg=MUTED, size=10, pad=(16,11)).pack(side="left")
        self._btn(acts, "Supprimer", lambda: self._delete(self.svc), bg="#2a1010", fg=RED, size=10, pad=(16,11)).pack(side="left", padx=10)
        burn(snapshot)

    def _interface_edition(self, nom_service):
        for w in self._panel.winfo_children(): w.destroy()
        snapshot = self._get_decrypted_data_snapshot()
        info = snapshot.get(nom_service, {"user":"","pw":"","url":""})
        wrap = tk.Frame(self._panel, bg=BG, padx=40, pady=36); wrap.pack(fill="both", expand=True)
        self._label(wrap, "Edition" if nom_service else "Nouveau", 20, bold=True).pack(anchor="w", pady=(0,20))
        
        def champ(parent, titre, val):
            self._label(parent, titre, 8, color=MUTED).pack(anchor="w")
            e = self._entry(parent, w=36); e.insert(0, val if val is not None else ""); e.pack(fill="x", pady=(4,16))
            return e
            
        e_srv = champ(wrap, "SERVICE", nom_service if nom_service else ""); e_usr = champ(wrap, "IDENTIFIANT", info.get("user", ""))
        pw_f = tk.Frame(wrap, bg=BG); pw_f.pack(fill="x"); self._label(pw_f, "MOT DE PASSE", 8, color=MUTED).pack(anchor="w")
        e_pwd = self._entry(pw_f, w=26); e_pwd.insert(0, info.get("pw", "")); e_pwd.pack(side="left", fill="x", expand=True, pady=(4,16))
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
            current_snapshot = self._get_decrypted_data_snapshot()
            if nom_service and nom_service != s:
                if nom_service in current_snapshot: del current_snapshot[nom_service]
            current_snapshot[s] = {"user":u, "pw":pw, "url":url}
            self.svc = s
            self._write_snapshot_to_disk(current_snapshot)
            self._refresh_list()
            self._load_svc()
            
        self._btn(wrap, "Sauvegarder", save, bg=GREEN, size=11, pad=(20,12)).pack(fill="x", pady=(20,0))
        burn(snapshot)

    def _delete(self, svc):
        if messagebox.askyesno("Confirmation", "Supprimer ?"):
            current_snapshot = self._get_decrypted_data_snapshot()
            if svc in current_snapshot: del current_snapshot[svc]
            self._write_snapshot_to_disk(current_snapshot)
            self._refresh_list()
            self._empty_panel()

    def _write_snapshot_to_disk(self, current_snapshot):
        p = dict(current_snapshot)
        p["__meta__"] = {"username": self.username}
        sauvegarder_base(self.ca, self.cc, p, self.salt)
        self._raw_encrypted_db = lire_base_brute()
        burn(p); burn(current_snapshot)


class AppLogin:
    def __init__(self, root):
        self.root = root
        self.root.title("VilksPass - Authentification")
        self.root.geometry("1060x660")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self._tries = 0
        self._lock = 0.0
        
        self.root.update()
        try:
            hwnd = int(self.root.frame(), 16)
            Activer_Anti_Capture(hwnd)
        except:
            pass
            
        session_auto = charger_session_locale()
        if session_auto:
            paquet, ca, cc, username = session_auto
            burn(paquet)
            self._switch_to_vault(username, ca.hex(), cc.hex())
            return
            
        if not os.path.exists(DB_FILE):
            self._pg_creation()
        else:
            self._pg_login()

    def _clear(self):
        for w in self.root.winfo_children(): w.destroy()

    def _entry(self, parent, show="", w=36):
        e = tk.Entry(parent, show=show, font=(F,11), bg=INPUT, fg=TEXT,
                     insertbackground=TEXT, relief="flat", bd=10,
                     highlightthickness=0, width=w)
        try:
            e.tk.call(e._w, "configure", "-isameffective", "0")
        except:
            pass
        return e

    def _btn(self, parent, text, cmd, bg=ACCENT, fg=WHITE, size=10, pad=(14,9)):
        return tk.Button(parent, text=text, command=cmd,
                         font=(F, size, "bold"), bg=bg, fg=fg,
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
        tk.Frame(left, bg=BG).pack(expand=True)
        
        form = tk.Frame(right, bg=CARD, padx=52); form.pack(fill="both", expand=True)
        tk.Frame(form, bg=CARD).pack(expand=True)
        inner_form = tk.Frame(form, bg=CARD); inner_form.pack(fill="x")
        self._label(inner_form, "Creer votre coffre", 20, bold=True).pack(anchor="w", pady=(0,6))
        self._label(inner_form, "NOM D'UTILISATEUR", 8, color=MUTED).pack(anchor="w")
        e_user = self._entry(inner_form, w=38); e_user.pack(fill="x", pady=(4,18)); e_user.focus()
        self._label(inner_form, "MOT DE PASSE MAITRE", 8, color=MUTED).pack(anchor="w")
        e_pwd = self._entry(inner_form, show="*", w=38); e_pwd.pack(fill="x", pady=(4,4))
        self._label(inner_form, "CONFIRMER", 8, color=MUTED).pack(anchor="w", pady=(10,0))
        e_conf = self._entry(inner_form, show="*", w=38); e_conf.pack(fill="x", pady=(4,4))
        lbl_err = tk.Label(inner_form, text="", font=(F,9), bg=CARD, fg=RED); lbl_err.pack(anchor="w", pady=(6,0))
        
        def creer():
            u=e_user.get().strip(); p=e_pwd.get(); pc=e_conf.get()
            if not u or not p or not pc: lbl_err.config(text="Tous les champs requis."); return
            if p != pc: lbl_err.config(text="Ecart mots de passe."); return
            errs = valider_mdp(p)
            if errs: lbl_err.config(text="Criteres non respectes."); return
            salt = os.urandom(SALT_SIZE); ca, cc = deriver_cles(u, p, salt)
            paquet = {"__meta__": {"username": u}}
            sauvegarder_base(ca, cc, paquet, salt)
            self._switch_to_vault(u, ca.hex(), cc.hex())
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
        tk.Checkbutton(inner_form, text="Rester connecté", variable=self.var_rester, 
                       bg=CARD, fg=TEXT, selectcolor=INPUT, font=(F, 9), bd=0).pack(anchor="w", pady=(4,0))
        self._lbl_err = tk.Label(inner_form, text="", font=(F,9), bg=CARD, fg=RED); self._lbl_err.pack(anchor="w", pady=(6,0))
        self._btn(inner_form, "Deverrouiller", self._login, size=11, pad=(20,12)).pack(fill="x", pady=(16,0))
        self._ep.bind("<Return>", lambda _: self._login())
        tk.Frame(form, bg=CARD).pack(expand=True)

    def _login(self):
        restant = self._lock - time.time()
        if restant > 0: return
        u = self._eu.get().strip(); mp = self._ep.get()
        res, ca, cc = lire_base(u, mp)
        if res is None:
            self._tries += 1
            if self._tries >= MAX_TENTATIVES: self._lock = time.time() + DELAI_LOCK_SEC; self._tries = 0
            return
        if self.var_rester.get(): creer_session_locale(u, ca, cc)
        self._switch_to_vault(u, ca.hex(), cc.hex())

    def _switch_to_vault(self, username, ca_hex, cc_hex):
        global _GLOBAL_CA, _GLOBAL_CC
        self._clear()
        
        _GLOBAL_CA = bytearray.fromhex(ca_hex)
        _GLOBAL_CC = bytearray.fromhex(cc_hex)
        Verrouiller_Memoire_Physique(_GLOBAL_CA)
        Verrouiller_Memoire_Physique(_GLOBAL_CC)
        
        self.root.title("VilksPass")
        AppVault(self.root, username, _GLOBAL_CA, _GLOBAL_CC)

if __name__ == "__main__":
    root = tk.Tk()
    AppLogin(root)
    root.mainloop()