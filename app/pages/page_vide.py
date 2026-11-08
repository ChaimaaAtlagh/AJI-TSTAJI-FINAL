"""
page_vide.py
Page provisoire affichée tant que la vraie page n'est pas écrite.
"""

import tkinter as tk

from app import theme


class PageVide(tk.Frame):
    """Une page = un Frame Tkinter, affiché ou caché par la fenêtre principale."""

    def __init__(self, parent, app, titre):
        super().__init__(parent, bg=theme.FOND)

        tk.Label(self, text=titre, font=theme.TITRE,
                 fg=theme.MARINE, bg=theme.FOND).pack(pady=(120, 10))
        tk.Label(self, text="Page en construction", font=theme.SOUS_TITRE,
                 fg=theme.TEXTE_CLAIR, bg=theme.FOND).pack()

        # Preuve que le dataset est bien partagé avec les pages
        tk.Label(self, text=f"{len(app.donnees)} entreprises chargées depuis data_nettoyee.xlsx",
                 font=theme.NORMAL, fg=theme.BLEU, bg=theme.FOND).pack(pady=20)