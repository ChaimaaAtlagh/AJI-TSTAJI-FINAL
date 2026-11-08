"""
markdown.py
Affiche proprement les réponses de l'IA, qui sont écrites en Markdown :
titres (###), gras (**...**), italique (*...*), listes, listes numérotées,
tableaux (| a | b |) et lignes de séparation.

Utilisation dans une bulle de message :
    from app.markdown import afficher_markdown
    zone = afficher_markdown(bulle, texte, couleur_fond="#FFFFFF", couleur_texte="#1F2A44")
    zone.pack(fill="x", padx=12, pady=(0, 10))
"""
import re

_MOTIF_INLINE = re.compile(r"(\*\*(.+?)\*\*|`([^`]+)`|\*([^*\s][^*]*?)\*)")
_SEPARATEUR_TABLEAU = re.compile(r"^:?-{2,}:?$")


def _inline(texte):
    """Découpe une ligne en segments (texte, style) : style = '', 'gras', 'italique' ou 'code'."""
    segments, pos = [], 0
    for m in _MOTIF_INLINE.finditer(texte):
        if m.start() > pos:
            segments.append((texte[pos:m.start()], ""))
        if m.group(2) is not None:
            segments.append((m.group(2), "gras"))
        elif m.group(3) is not None:
            segments.append((m.group(3), "code"))
        else:
            segments.append((m.group(4), "italique"))
        pos = m.end()
    if pos < len(texte):
        segments.append((texte[pos:], ""))
    return segments or [("", "")]


def _cellules(ligne):
    ligne = ligne.strip()
    if ligne.startswith("|"):
        ligne = ligne[1:]
    if ligne.endswith("|"):
        ligne = ligne[:-1]
    return [c.strip() for c in ligne.split("|")]


def _est_separateur(cellules):
    return bool(cellules) and all(_SEPARATEUR_TABLEAU.match(c) for c in cellules if c != "") \
        and any(c != "" for c in cellules)


def _tableau_en_blocs(lignes):
    """Un tableau devient une suite lisible : le 1er champ en gras, puis « En-tête : valeur »."""
    lignes_cell = [_cellules(l) for l in lignes]
    entete, donnees = None, lignes_cell
    if len(lignes_cell) >= 2 and _est_separateur(lignes_cell[1]):
        entete, donnees = lignes_cell[0], lignes_cell[2:]
    blocs = []
    for cellules in donnees:
        if not cellules or _est_separateur(cellules):
            continue
        if entete is None:
            blocs.append(("para", _inline(" — ".join(c for c in cellules if c))))
            continue
        blocs.append(("para", [(t, "gras" if s == "" else s) for t, s in _inline(cellules[0])]))
        for j in range(1, len(cellules)):
            if not cellules[j]:
                continue
            nom = entete[j] if j < len(entete) else ""
            segs = ([(nom + " : ", "gras")] if nom else []) + _inline(cellules[j])
            blocs.append(("puce", 1, segs))
    return blocs


def analyser_markdown(texte):
    """Transforme le texte en liste de blocs. Cette fonction n'utilise pas Tkinter."""
    lignes = (texte or "").replace("\r", "").split("\n")
    blocs, i = [], 0
    while i < len(lignes):
        brut = lignes[i]
        s = brut.strip()
        if not s:
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            blocs.append(("titre", min(len(m.group(1)), 3), _inline(m.group(2).strip("# "))))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            blocs.append(("separateur",))
            i += 1
            continue
        if s.startswith("|"):
            tableau = []
            while i < len(lignes) and lignes[i].strip().startswith("|"):
                tableau.append(lignes[i])
                i += 1
            blocs.extend(_tableau_en_blocs(tableau))
            continue
        m = re.match(r"^(\s*)[-*•]\s+(.*)$", brut)
        if m:
            niveau = min(len(m.group(1).replace("\t", "    ")) // 2, 2)
            blocs.append(("puce", niveau, _inline(m.group(2))))
            i += 1
            continue
        m = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", brut)
        if m:
            niveau = min(len(m.group(1).replace("\t", "    ")) // 2, 2)
            blocs.append(("num", niveau, m.group(2), _inline(m.group(3))))
            i += 1
            continue
        blocs.append(("para", _inline(s)))
        i += 1
    return blocs


def afficher_markdown(parent, texte, couleur_fond="#FFFFFF", couleur_texte="#1F2A44",
                      couleur_accent="#1F6FEB", police="Segoe UI", taille=14, largeur=90):
    """Crée un widget de texte (lecture seule, sélectionnable) avec le Markdown mis en forme."""
    import tkinter as tk
    from tkinter import font as tkfont

    zone = tk.Text(parent, wrap="word", width=largeur, height=1, bg=couleur_fond, fg=couleur_texte,
                   bd=0, highlightthickness=0, relief="flat", padx=0, pady=0, cursor="arrow",
                   font=(police, taille), insertwidth=0, takefocus=0)

    normal = tkfont.Font(family=police, size=taille)
    gras = tkfont.Font(family=police, size=taille, weight="bold")
    italique = tkfont.Font(family=police, size=taille, slant="italic")
    code = tkfont.Font(family="Consolas", size=max(taille - 1, 9))
    zone._polices = (normal, gras, italique, code)   # garder une référence

    zone.tag_configure("gras", font=gras)
    zone.tag_configure("italique", font=italique)
    zone.tag_configure("code", font=code, background="#EAF0FB")
    zone.tag_configure("para", spacing3=8)
    for n, (extra, haut) in {1: (6, 10), 2: (4, 8), 3: (2, 6)}.items():
        f = tkfont.Font(family=police, size=taille + extra, weight="bold")
        zone._polices += (f,)
        zone.tag_configure("titre%d" % n, font=f, foreground=couleur_accent if n < 3 else couleur_texte,
                           spacing1=haut, spacing3=6)
    for niveau in range(3):
        g1, g2 = 14 + niveau * 22, 30 + niveau * 22
        zone.tag_configure("puce%d" % niveau, lmargin1=g1, lmargin2=g2, spacing3=4)
    zone.tag_configure("sep", foreground="#B8C4DA", spacing3=8)

    def segments(liste, tags_bloc):
        for contenu, style in liste:
            zone.insert("end", contenu, tuple(tags_bloc) + ((style,) if style else ()))

    for bloc in analyser_markdown(texte):
        type_ = bloc[0]
        if type_ == "titre":
            segments(bloc[2], ["titre%d" % bloc[1]])
        elif type_ == "puce":
            zone.insert("end", "•  ", ("puce%d" % bloc[1],))
            segments(bloc[2], ["puce%d" % bloc[1]])
        elif type_ == "num":
            zone.insert("end", bloc[2] + ".  ", ("puce%d" % bloc[1],))
            segments(bloc[3], ["puce%d" % bloc[1]])
        elif type_ == "separateur":
            zone.insert("end", "─" * 40, ("sep",))
        else:
            segments(bloc[1], ["para"])
        zone.insert("end", "\n")
    if zone.get("end-2c", "end-1c") == "\n":      # retire le dernier saut de ligne en trop
        zone.delete("end-2c", "end-1c")
    zone.configure(state="disabled")

    def ajuster(event=None):
        """Adapte la hauteur au nombre de lignes affichées (pas de défilement interne)."""
        try:
            res = zone.count("1.0", "end-1c", "displaylines")
            n = max(int(res[0]) if res else 1, 1)
            if int(zone.cget("height")) != n:
                zone.configure(height=n)
        except tk.TclError:
            pass

    zone.bind("<Configure>", ajuster)
    zone.after(40, ajuster)
    return zone