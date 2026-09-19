import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import requests

from fabrik_frontend import api


class App(tk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master)

        master.title("Wartungsmanagement")
        master.minsize(1000, 650)

        self.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10,
        )

        self._build_api_key_area()

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self._build_statistics_tab(notebook)
        self._build_geraete_tab(notebook)
        self._build_wartungsplan_tab(notebook)
        self._build_wartungen_tab(notebook)
        self._build_standorte_tab(notebook)
        self._build_techniker_tab(notebook)
    # =========================================================
    # Allgemeiner Bereich
    # =========================================================

    def _build_api_key_area(self):
        frame = ttk.LabelFrame(self, text="API-Zugang")
        frame.pack(fill=tk.X)

        ttk.Label(frame, text="X-API-Key:").pack(
            side=tk.LEFT,
            padx=(8, 4),
            pady=6,
        )

        self._api_key_entry = ttk.Entry(frame, width=40, show="*")
        self._api_key_entry.pack(
            side=tk.LEFT,
            padx=4,
            pady=6,
        )

        ttk.Button(
            frame,
            text="Übernehmen",
            command=self._set_api_key,
        ).pack(side=tk.LEFT, padx=4)

    def _set_api_key(self):
        api.set_api_key(self._api_key_entry.get())
        messagebox.showinfo(
            "API-Key",
            "API-Key wurde übernommen.",
        )

    # =========================================================
    # Hilfsmethoden
    # =========================================================

    def _labeled_entry(
        self,
        parent,
        label: str,
        row: int,
    ) -> ttk.Entry:
        ttk.Label(
            parent,
            text=f"{label}:",
        ).grid(
            row=row,
            column=0,
            padx=8,
            pady=4,
            sticky=tk.E,
        )

        entry = ttk.Entry(parent, width=30)
        entry.grid(
            row=row,
            column=1,
            padx=8,
            pady=4,
            sticky=tk.W,
        )

        return entry

    def _configure_tree(self, tree, headings):
        for column, heading, width in headings:
            tree.heading(column, text=heading)
            tree.column(
                column,
                width=width,
                anchor=tk.CENTER,
            )

    def _clear_tree(self, tree):
        tree.delete(*tree.get_children())

    def _required(
        self,
        entry: ttk.Entry,
        feldname: str,
    ) -> str:
        wert = entry.get().strip()

        if not wert:
            raise ValueError(
                f"Das Feld '{feldname}' darf nicht leer sein."
            )

        return wert

    def _required_int(
        self,
        entry: ttk.Entry,
        feldname: str,
    ) -> int:
        wert = self._required(entry, feldname)

        try:
            return int(wert)
        except ValueError as error:
            raise ValueError(
                f"'{feldname}' muss eine ganze Zahl sein."
            ) from error

    def _show_error(self, error: Exception):
        if isinstance(error, requests.HTTPError):
            response = error.response

            try:
                detail = response.json().get(
                    "detail",
                    response.text,
                )
            except ValueError:
                detail = response.text

            messagebox.showerror(
                "API-Fehler",
                f"HTTP {response.status_code}: {detail}",
            )
            return

        if isinstance(error, requests.ConnectionError):
            messagebox.showerror(
                "Verbindungsfehler",
                "Die API unter http://localhost:8000 ist nicht erreichbar.",
            )
            return

        messagebox.showerror("Fehler", str(error))
    # =========================================================
    # Statistik
    # =========================================================

    def _build_statistics_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Statistik")

        filter_frame = ttk.LabelFrame(frame, text="Zeitraum")
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        aktuelles_jahr = date.today().year

        self._stat_von = self._labeled_entry(
            filter_frame,
            "Von (JJJJ-MM-TT)",
            0,
        )
        self._stat_von.insert(0, f"{aktuelles_jahr}-01-01")

        self._stat_bis = self._labeled_entry(
            filter_frame,
            "Bis (JJJJ-MM-TT)",
            1,
        )
        self._stat_bis.insert(0, f"{aktuelles_jahr}-12-31")

        button_frame = ttk.Frame(filter_frame)
        button_frame.grid(
            row=0,
            column=2,
            rowspan=2,
            padx=10,
        )

        ttk.Button(
            button_frame,
            text="Nach Standort",
            command=self._load_statistics_standorte,
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            button_frame,
            text="Nach Techniker",
            command=self._load_statistics_techniker,
        ).pack(fill=tk.X, pady=2)

        columns = (
            "art",
            "id",
            "bezeichnung",
            "durchgefuehrt",
            "geplant",
        )

        self._statistics_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
        )

        headings = [
            ("art", "Auswertung", 130),
            ("id", "ID", 70),
            ("bezeichnung", "Techniker/Standort", 350),
            ("durchgefuehrt", "Durchgeführt", 120),
            ("geplant", "Offen geplant", 120),
        ]

        self._configure_tree(self._statistics_tree, headings)
        self._statistics_tree.pack(fill=tk.BOTH, expand=True)

    def _load_statistics_standorte(self):
        try:
            von, bis = self._get_statistik_zeitraum()

            daten = api.get_Statistik_Wartungen_pro_Standort(
                von,
                bis,
            )

            self._clear_tree(self._statistics_tree)

            for eintrag in daten:
                adresse = (
                    f"{eintrag['plz']} {eintrag['stadt']}, "
                    f"{eintrag['strasse']} "
                    f"{eintrag['hausnummer']}"
                )

                self._statistics_tree.insert(
                    "",
                    tk.END,
                    values=(
                        "Standort",
                        eintrag["standort_id"],
                        adresse,
                        eintrag["durchgefuehrte_wartungen"],
                        eintrag["geplante_offene_wartungen"],
                    ),
                )

        except Exception as error:
            self._show_error(error)

    def _load_statistics_techniker(self):
        try:
            von, bis = self._get_statistik_zeitraum()

            daten = api.get_Statistik_Wartungen_pro_Techniker(
                von,
                bis,
            )

            self._clear_tree(self._statistics_tree)

            for eintrag in daten:
                self._statistics_tree.insert(
                    "",
                    tk.END,
                    values=(
                        "Techniker",
                        eintrag["techniker_id"],
                        eintrag["techniker_name"],
                        eintrag["anzahl_wartungen"],
                        "",
                    ),
                )

        except Exception as error:
            self._show_error(error)

    def _get_statistik_zeitraum(self):
        von = self._required(self._stat_von, "Von")
        bis = self._required(self._stat_bis, "Bis")

        if von > bis:
            raise ValueError(
                "'Von' darf nicht nach 'Bis' liegen."
            )

        return von, bis

    # =========================================================
    # Geräte
    # =========================================================

    def _build_geraete_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Geräte")

        search = ttk.LabelFrame(frame, text="Geräte anzeigen")
        search.pack(fill=tk.X, pady=(0, 8))

        self._geraet_suche_seriennummer = self._labeled_entry(
            search,
            "Seriennummer",
            0,
        )

        ttk.Button(
            search,
            text="Gerät suchen",
            command=self._load_geraet,
        ).grid(row=0, column=2, padx=5)

        self._geraet_suche_standort = self._labeled_entry(
            search,
            "Standort-ID",
            1,
        )

        ttk.Button(
            search,
            text="Geräte am Standort",
            command=self._load_standort_geraete,
        ).grid(row=1, column=2, padx=5)

        columns = (
            "seriennummer",
            "hersteller",
            "typ",
            "intervall",
            "standort",
            "naechste_wartung",
        )

        self._geraete_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=9,
        )

        self._configure_tree(
            self._geraete_tree,
            [
                ("seriennummer", "Seriennummer", 140),
                ("hersteller", "Hersteller", 130),
                ("typ", "Typ", 130),
                ("intervall", "Intervall", 90),
                ("standort", "Standort", 260),
                ("naechste_wartung", "Nächste Wartung", 130),
            ],
        )
        self._geraete_tree.pack(fill=tk.BOTH, expand=True)

        form = ttk.LabelFrame(frame, text="Neues Gerät")
        form.pack(fill=tk.X, pady=8)

        self._g_seriennummer = self._labeled_entry(
            form, "Seriennummer", 0
        )
        self._g_hersteller = self._labeled_entry(
            form, "Hersteller", 1
        )
        self._g_typ = self._labeled_entry(form, "Typ", 2)
        self._g_intervall = self._labeled_entry(
            form, "Wartungsintervall in Tagen", 3
        )
        self._g_standort = self._labeled_entry(
            form, "Standort-ID", 4
        )

        ttk.Button(
            form,
            text="Gerät anlegen",
            command=self._create_geraet,
        ).grid(row=5, column=1, pady=6, sticky=tk.W)

    def _load_geraet(self):
        try:
            seriennummer = self._required(
                self._geraet_suche_seriennummer,
                "Seriennummer",
            )

            geraet = api.get_Geraet(seriennummer)
            self._clear_tree(self._geraete_tree)

            adresse = (
                f"{geraet['plz']} {geraet['stadt']}, "
                f"{geraet['strasse']} {geraet['hausnummer']}"
            )

            self._geraete_tree.insert(
                "",
                tk.END,
                values=(
                    geraet["seriennummer"],
                    geraet["hersteller"],
                    geraet["typ"],
                    geraet["wartungsintervall"],
                    adresse,
                    geraet.get("naechste_wartung_datum", ""),
                ),
            )

        except Exception as error:
            self._show_error(error)

    def _load_standort_geraete(self):
        try:
            standort_id = self._required_int(
                self._geraet_suche_standort,
                "Standort-ID",
            )

            geraete = api.get_StandortGeraete(standort_id)
            self._clear_tree(self._geraete_tree)

            for geraet in geraete:
                self._geraete_tree.insert(
                    "",
                    tk.END,
                    values=(
                        geraet["seriennummer"],
                        geraet["hersteller"],
                        geraet["typ"],
                        geraet["wartungsintervall"],
                        geraet["standort_id"],
                        "",
                    ),
                )

        except Exception as error:
            self._show_error(error)

    def _create_geraet(self):
        try:
            api.post_Geraet(
                seriennummer=self._required(
                    self._g_seriennummer,
                    "Seriennummer",
                ),
                hersteller=self._required(
                    self._g_hersteller,
                    "Hersteller",
                ),
                typ=self._required(self._g_typ, "Typ"),
                wartungsintervall=self._required_int(
                    self._g_intervall,
                    "Wartungsintervall",
                ),
                standort_id=self._required_int(
                    self._g_standort,
                    "Standort-ID",
                ),
            )

            messagebox.showinfo(
                "Erfolg",
                "Gerät wurde angelegt.",
            )

        except Exception as error:
            self._show_error(error)

    # =========================================================
    # Wartungsplan
    # =========================================================

    def _build_wartungsplan_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Wartungsplan")

        filter_frame = ttk.LabelFrame(
            frame,
            text="Wartungsplan anzeigen",
        )
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        self._wp_von = self._labeled_entry(
            filter_frame, "Von", 0
        )
        self._wp_bis = self._labeled_entry(
            filter_frame, "Bis", 1
        )
        self._wp_techniker_filter = self._labeled_entry(
            filter_frame, "Techniker-ID", 2
        )

        ttk.Button(
            filter_frame,
            text="Zeitraum laden",
            command=self._load_wartungsplan_zeitraum,
        ).grid(row=0, column=2, padx=5)

        ttk.Button(
            filter_frame,
            text="Techniker laden",
            command=self._load_wartungsplan_techniker,
        ).grid(row=1, column=2, padx=5)

        ttk.Button(
            filter_frame,
            text="Überfällige laden",
            command=self._load_ueberfaellige,
        ).grid(row=2, column=2, padx=5)

        columns = (
            "id",
            "datum",
            "seriennummer",
            "techniker_id",
            "techniker",
            "standort",
            "status",
        )

        self._wartungsplan_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=9,
        )

        self._configure_tree(
            self._wartungsplan_tree,
            [
                ("id", "Plan-ID", 70),
                ("datum", "Datum", 100),
                ("seriennummer", "Seriennummer", 130),
                ("techniker_id", "Techniker-ID", 90),
                ("techniker", "Techniker", 150),
                ("standort", "Standort", 210),
                ("status", "Status", 110),
            ],
        )

        self._wartungsplan_tree.pack(fill=tk.BOTH, expand=True)

        form = ttk.LabelFrame(
            frame,
            text="Wartung planen oder ändern",
        )
        form.pack(fill=tk.X, pady=8)

        self._wp_id = self._labeled_entry(form, "Plan-ID", 0)
        self._wp_datum = self._labeled_entry(form, "Datum", 1)
        self._wp_seriennummer = self._labeled_entry(
            form, "Seriennummer", 2
        )
        self._wp_techniker_id = self._labeled_entry(
            form, "Techniker-ID", 3
        )

        buttons = ttk.Frame(form)
        buttons.grid(row=4, column=1, pady=6, sticky=tk.W)

        ttk.Button(
            buttons,
            text="Planen",
            command=self._create_wartungsplan,
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            buttons,
            text="Ändern",
            command=self._update_wartungsplan,
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            buttons,
            text="Löschen",
            command=self._delete_wartungsplan,
        ).pack(side=tk.LEFT, padx=3)

    def _load_wartungsplan_zeitraum(self):
        try:
            daten = api.get_Wartungsplan(
                self._required(self._wp_von, "Von"),
                self._required(self._wp_bis, "Bis"),
            )
            self._insert_wartungsplan(daten)

        except Exception as error:
            self._show_error(error)

    def _load_wartungsplan_techniker(self):
        try:
            daten = api.get_Wartungsplan_Techniker(
                self._required_int(
                    self._wp_techniker_filter,
                    "Techniker-ID",
                )
            )
            self._insert_wartungsplan(daten)

        except Exception as error:
            self._show_error(error)

    def _load_ueberfaellige(self):
        try:
            daten = api.get_WartungsplanUeberfaellige()
            self._insert_wartungsplan(daten, "Überfällig")

        except Exception as error:
            self._show_error(error)

    def _insert_wartungsplan(self, daten, standard_status="Geplant"):
        self._clear_tree(self._wartungsplan_tree)

        for eintrag in daten:
            standort = ""

            if eintrag.get("stadt"):
                standort = (
                    f"{eintrag.get('plz', '')} "
                    f"{eintrag.get('stadt', '')}, "
                    f"{eintrag.get('strasse', '')} "
                    f"{eintrag.get('hausnummer', '')}"
                )

            status_text = standard_status

            if eintrag.get("durchgefuehrt") is True:
                status_text = "Durchgeführt"

            self._wartungsplan_tree.insert(
                "",
                tk.END,
                values=(
                    eintrag.get("wartungsplan_id", eintrag.get("id")),
                    eintrag.get("datum"),
                    eintrag.get(
                        "seriennummer",
                        eintrag.get("geraet_seriennummer"),
                    ),
                    eintrag.get("techniker_id"),
                    eintrag.get("techniker_name", ""),
                    standort,
                    status_text,
                ),
            )

    def _create_wartungsplan(self):
        try:
            api.post_Wartungsplan(
                datum=self._required(self._wp_datum, "Datum"),
                geraet_seriennummer=self._required(
                    self._wp_seriennummer,
                    "Seriennummer",
                ),
                techniker_id=self._required_int(
                    self._wp_techniker_id,
                    "Techniker-ID",
                ),
            )

            messagebox.showinfo(
                "Erfolg",
                "Wartung wurde geplant.",
            )

        except Exception as error:
            self._show_error(error)

    def _update_wartungsplan(self):
        try:
            api.put_Wartungsplan(
                wartungsplan_id=self._required_int(
                    self._wp_id,
                    "Plan-ID",
                ),
                datum=self._required(self._wp_datum, "Datum"),
                techniker_id=self._required_int(
                    self._wp_techniker_id,
                    "Techniker-ID",
                ),
            )

            messagebox.showinfo(
                "Erfolg",
                "Wartungsplan wurde geändert.",
            )

        except Exception as error:
            self._show_error(error)

    def _delete_wartungsplan(self):
        try:
            wartungsplan_id = self._required_int(
                self._wp_id,
                "Plan-ID",
            )

            bestaetigt = messagebox.askyesno(
                "Wartungsplan löschen",
                f"Wartungsplan {wartungsplan_id} wirklich löschen?",
            )

            if not bestaetigt:
                return

            api.delete_Wartungsplan(wartungsplan_id)

            messagebox.showinfo(
                "Erfolg",
                "Wartungsplan wurde gelöscht.",
            )

        except Exception as error:
            self._show_error(error)

    # =========================================================
    # Wartungen
    # =========================================================

    def _build_wartungen_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Wartungen")

        filter_frame = ttk.LabelFrame(
            frame,
            text="Wartungshistorie",
        )
        filter_frame.pack(fill=tk.X, pady=(0, 8))

        self._wartung_filter_seriennummer = self._labeled_entry(
            filter_frame,
            "Seriennummer",
            0,
        )

        ttk.Button(
            filter_frame,
            text="Historie laden",
            command=self._load_wartungshistorie,
        ).grid(row=0, column=2, padx=5)

        columns = (
            "id",
            "datum",
            "seriennummer",
            "techniker_id",
            "techniker",
            "ersatzgeraet",
            "plan_id",
        )

        self._wartungen_tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=10,
        )

        self._configure_tree(
            self._wartungen_tree,
            [
                ("id", "Wartungs-ID", 90),
                ("datum", "Datum", 100),
                ("seriennummer", "Seriennummer", 130),
                ("techniker_id", "Techniker-ID", 90),
                ("techniker", "Techniker", 160),
                ("ersatzgeraet", "Ersatzgerät", 130),
                ("plan_id", "Plan-ID", 80),
            ],
        )
        self._wartungen_tree.pack(fill=tk.BOTH, expand=True)

        form = ttk.LabelFrame(
            frame,
            text="Durchgeführte Wartung dokumentieren",
        )
        form.pack(fill=tk.X, pady=8)

        self._w_datum = self._labeled_entry(form, "Datum", 0)
        self._w_seriennummer = self._labeled_entry(
            form, "Seriennummer", 1
        )
        self._w_techniker_id = self._labeled_entry(
            form, "Techniker-ID", 2
        )
        self._w_ersatzgeraet = self._labeled_entry(
            form, "Ersatzgerät (optional)", 3
        )
        self._w_plan_id = self._labeled_entry(
            form, "Wartungsplan-ID (optional)", 4
        )

        ttk.Button(
            form,
            text="Wartung speichern",
            command=self._create_wartung,
        ).grid(row=5, column=1, pady=6, sticky=tk.W)

    def _load_wartungshistorie(self):
        try:
            seriennummer = self._required(
                self._wartung_filter_seriennummer,
                "Seriennummer",
            )

            daten = api.get_GeraetWartungen(seriennummer)
            self._clear_tree(self._wartungen_tree)

            for wartung in daten:
                self._wartungen_tree.insert(
                    "",
                    tk.END,
                    values=(
                        wartung["wartung_id"],
                        wartung["datum"],
                        wartung["seriennummer"],
                        wartung["techniker_id"],
                        wartung["techniker_name"],
                        wartung.get("ersatzgeraet", ""),
                        wartung.get("wartungsplan_id", ""),
                    ),
                )

        except Exception as error:
            self._show_error(error)

    def _create_wartung(self):
        try:
            plan_id_text = self._w_plan_id.get().strip()

            wartungsplan_id = (
                int(plan_id_text)
                if plan_id_text
                else None
            )

            api.post_Wartung(
                datum=self._required(self._w_datum, "Datum"),
                ersatzgeraet=(
                    self._w_ersatzgeraet.get().strip() or None
                ),
                geraet_seriennummer=self._required(
                    self._w_seriennummer,
                    "Seriennummer",
                ),
                techniker_id=self._required_int(
                    self._w_techniker_id,
                    "Techniker-ID",
                ),
                wartungsplan_id=wartungsplan_id,
            )

            messagebox.showinfo(
                "Erfolg",
                "Wartung wurde dokumentiert.",
            )

        except Exception as error:
            self._show_error(error)


    # =========================================================
    # Standorte
    # =========================================================

    def _build_standorte_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Standorte")

        table_frame = ttk.LabelFrame(
            frame,
            text="Vorhandene Standorte",
        )
        table_frame.pack(
            fill=tk.BOTH,
            expand=True,
            pady=(0, 8),
        )

        columns = (
            "id",
            "plz",
            "stadt",
            "strasse",
            "hausnummer",
        )

        self._standorte_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=12,
        )

        self._configure_tree(
            self._standorte_tree,
            [
                ("id", "Standort-ID", 100),
                ("plz", "PLZ", 100),
                ("stadt", "Stadt", 180),
                ("strasse", "Straße", 220),
                ("hausnummer", "Hausnummer", 120),
            ],
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self._standorte_tree.yview,
        )

        self._standorte_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self._standorte_tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(8, 0),
            pady=8,
        )

        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y,
            padx=(0, 8),
            pady=8,
        )

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(
            button_frame,
            text="Aktualisieren",
            command=self._load_standorte,
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            button_frame,
            text="Auswahl für Gerät übernehmen",
            command=self._select_standort,
        ).pack(side=tk.LEFT, padx=4)

        form = ttk.LabelFrame(
            frame,
            text="Neuen Standort anlegen",
        )
        form.pack(fill=tk.X)

        self._standort_plz = self._labeled_entry(
            form,
            "PLZ",
            0,
        )

        self._standort_stadt = self._labeled_entry(
            form,
            "Stadt",
            1,
        )

        self._standort_strasse = self._labeled_entry(
            form,
            "Straße",
            2,
        )

        self._standort_hausnummer = self._labeled_entry(
            form,
            "Hausnummer",
            3,
        )

        form_buttons = ttk.Frame(form)
        form_buttons.grid(
            row=4,
            column=1,
            pady=8,
            sticky=tk.W,
        )

        ttk.Button(
            form_buttons,
            text="Standort anlegen",
            command=self._create_standort,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            form_buttons,
            text="Eingaben leeren",
            command=self._clear_standort_form,
        ).pack(side=tk.LEFT, padx=5)

        self._load_standorte()

    def _load_standorte(self):
        try:
            standorte = api.get_Standorte()

            self._clear_tree(self._standorte_tree)

            for standort in standorte:
                self._standorte_tree.insert(
                    "",
                    tk.END,
                    values=(
                        standort["id"],
                        standort["plz"],
                        standort["stadt"],
                        standort["strasse"],
                        standort["hausnummer"],
                    ),
                )

        except Exception as error:
            self._show_error(error)

    def _create_standort(self):
        try:
            neuer_standort = api.post_Standort(
                plz=self._required(
                    self._standort_plz,
                    "PLZ",
                ),
                stadt=self._required(
                    self._standort_stadt,
                    "Stadt",
                ),
                strasse=self._required(
                    self._standort_strasse,
                    "Straße",
                ),
                hausnummer=self._required(
                    self._standort_hausnummer,
                    "Hausnummer",
                ),
            )

            messagebox.showinfo(
                "Erfolg",
                (
                    "Der Standort wurde angelegt.\n"
                    f"Standort-ID: {neuer_standort['id']}"
                ),
            )

            self._clear_standort_form()
            self._load_standorte()

        except Exception as error:
            self._show_error(error)

    def _clear_standort_form(self):
        entries = (
            self._standort_plz,
            self._standort_stadt,
            self._standort_strasse,
            self._standort_hausnummer,
        )

        for entry in entries:
            entry.delete(0, tk.END)

    def _select_standort(self):
        selected_items = self._standorte_tree.selection()

        if not selected_items:
            messagebox.showwarning(
                "Keine Auswahl",
                "Bitte wähle zuerst einen Standort aus.",
            )
            return

        selected_item = selected_items[0]

        values = self._standorte_tree.item(
            selected_item,
            "values",
        )

        standort_id = values[0]

        self._g_standort.delete(0, tk.END)
        self._g_standort.insert(0, standort_id)

        messagebox.showinfo(
            "Standort übernommen",
            (
                f"Standort {standort_id} wurde in das "
                "Formular zum Anlegen eines Geräts übernommen."
            ),
        )
    # =========================================================
    # Techniker
    # =========================================================

    def _build_techniker_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Techniker")

        self._techniker_daten = {}
        self._techniker_standorte = []
        self._techniker_bearbeiten_id = None

        # Tabelle
        table_frame = ttk.LabelFrame(
            frame,
            text="Vorhandene Techniker",
        )
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self._techniker_tree = ttk.Treeview(
            table_frame,
            columns=("id", "name", "standorte", "typen"),
            show="headings",
            selectmode="browse",
            height=8,
        )

        self._configure_tree(
            self._techniker_tree,
            [
                ("id", "Techniker-ID", 90),
                ("name", "Name", 200),
                ("standorte", "Standort-IDs", 220),
                ("typen", "Gerätetypen", 300),
            ],
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient=tk.VERTICAL,
            command=self._techniker_tree.yview,
        )
        self._techniker_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self._techniker_tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(8, 0),
            pady=8,
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=8)

        self._techniker_tree.bind(
            "<<TreeviewSelect>>",
            self._techniker_auswahl_laden,
        )

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(
            buttons,
            text="Aktualisieren",
            command=self._load_techniker,
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            buttons,
            text="ID in beide Formulare übernehmen",
            command=self._select_techniker,
        ).pack(side=tk.LEFT, padx=4)

        # Formular
        form = ttk.LabelFrame(
            frame,
            text="Techniker und Zuständigkeiten",
        )
        form.pack(fill=tk.X)

        self._techniker_modus = tk.StringVar(
            value="Neuer Techniker"
        )
        ttk.Label(
            form,
            textvariable=self._techniker_modus,
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            padx=8,
            pady=4,
            sticky=tk.W,
        )

        self._techniker_name = self._labeled_entry(
            form, "Name", 1
        )

        ttk.Label(
            form,
            text="Zuständige Standorte:",
        ).grid(
            row=2,
            column=0,
            padx=8,
            pady=4,
            sticky=tk.NE,
        )

        list_frame = ttk.Frame(form)
        list_frame.grid(
            row=2,
            column=1,
            padx=8,
            pady=4,
            sticky=tk.EW,
        )
        form.columnconfigure(1, weight=1)

        # Jeder Klick schaltet einen Standort an oder aus.
        # exportselection=False erhält die Auswahl beim Feldwechsel.
        self._techniker_standort_liste = tk.Listbox(
            list_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=5,
            width=65,
        )

        list_scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self._techniker_standort_liste.yview,
        )
        self._techniker_standort_liste.configure(
            yscrollcommand=list_scrollbar.set
        )

        self._techniker_standort_liste.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True
        )
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._techniker_typen = self._labeled_entry(
            form, "Gerätetypen (mit ; trennen)", 3
        )

        ttk.Label(
            form,
            text=(
                "Beispiel: Drucker; Scanner; Router — "
                "Schreibweise wie beim Gerät verwenden."
            ),
        ).grid(
            row=4,
            column=1,
            padx=8,
            sticky=tk.W,
        )

        form_buttons = ttk.Frame(form)
        form_buttons.grid(
            row=5, column=1, padx=8, pady=8, sticky=tk.W
        )

        ttk.Button(
            form_buttons,
            text="Neu / Eingaben leeren",
            command=self._clear_techniker_form,
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            form_buttons,
            text="Speichern",
            command=self._save_techniker,
        ).pack(side=tk.LEFT)

        ttk.Label(
            frame,
            text=(
                "Tabelleneintrag auswählen zum Bearbeiten. "
                "Aktualisieren verwirft ungespeicherte Eingaben."
            ),
        ).pack(anchor=tk.W, pady=4)

        self.after_idle(self._load_techniker)

    def _load_techniker(self):
        try:
            # Erst beide Abfragen erfolgreich abschließen,
            # bevor die vorhandene Anzeige verändert wird.
            techniker = api.get_Techniker()
            standorte = api.get_Standorte()

            self._techniker_daten = {
                str(eintrag["id"]): eintrag
                for eintrag in techniker
            }
            self._techniker_standorte = standorte

            self._clear_techniker_form()

            for item in self._techniker_tree.get_children():
                self._techniker_tree.delete(item)

            self._techniker_standort_liste.delete(0, tk.END)

            for standort in standorte:
                self._techniker_standort_liste.insert(
                    tk.END,
                    (
                        f"{standort['id']}: "
                        f"{standort['plz']} {standort['stadt']}, "
                        f"{standort['strasse']} "
                        f"{standort['hausnummer']}"
                    ),
                )

            for eintrag in techniker:
                self._techniker_tree.insert(
                    "",
                    tk.END,
                    iid=str(eintrag["id"]),
                    values=(
                        eintrag["id"],
                        eintrag["name"],
                        ", ".join(
                            str(wert)
                            for wert in eintrag["standort_ids"]
                        ),
                        "; ".join(eintrag["geraetetypen"]),
                    ),
                )

        except Exception as error:
            self._show_error(error)

    def _techniker_auswahl_laden(self, event=None):
        auswahl = self._techniker_tree.selection()

        if not auswahl:
            return

        daten = self._techniker_daten.get(auswahl[0])
        if daten is None:
            return

        self._techniker_bearbeiten_id = daten["id"]
        self._techniker_modus.set(
            f"Techniker {daten['id']} bearbeiten"
        )

        self._techniker_name.delete(0, tk.END)
        self._techniker_name.insert(0, daten["name"])

        self._techniker_typen.delete(0, tk.END)The
        self._techniker_typen.insert(
            0, "; ".join(daten["geraetetypen"])
        )

        self._techniker_standort_liste.selection_clear(
            0, tk.END
        )

        zugeordnet = set(daten["standort_ids"])

        for index, standort in enumerate(
            self._techniker_standorte
        ):
            if standort["id"] in zugeordnet:
                self._techniker_standort_liste.selection_set(index)

    def _clear_techniker_form(self):
        self._techniker_bearbeiten_id = None
        self._techniker_modus.set("Neuer Techniker")

        self._techniker_name.delete(0, tk.END)
        self._techniker_typen.delete(0, tk.END)
        self._techniker_standort_liste.selection_clear(
            0, tk.END
        )

        auswahl = self._techniker_tree.selection()
        if auswahl:
            self._techniker_tree.selection_remove(*auswahl)

    def _save_techniker(self):
        try:
            name = self._required(
                self._techniker_name, "Name"
            )

            standort_ids = [
                self._techniker_standorte[index]["id"]
                for index in
                self._techniker_standort_liste.curselection()
            ]

            geraetetypen = sorted({
                typ.strip()
                for typ in self._techniker_typen.get().split(";")
                if typ.strip()
            })

            if len(name) > 150:
                raise ValueError(
                    "Der Name darf höchstens 150 Zeichen haben."
                )

            if any(len(typ) > 100 for typ in geraetetypen):
                raise ValueError(
                    "Ein Gerätetyp darf höchstens 100 Zeichen haben."
                )

            if self._techniker_bearbeiten_id is None:
                ergebnis = api.post_Techniker(
                    name=name,
                    standort_ids=standort_ids,
                    geraetetypen=geraetetypen,
                )
            else:
                ergebnis = api.put_Techniker(
                    techniker_id=self._techniker_bearbeiten_id,
                    name=name,
                    standort_ids=standort_ids,
                    geraetetypen=geraetetypen,
                )

        except Exception as error:
            self._show_error(error)
            return

        messagebox.showinfo(
            "Gespeichert",
            f"Techniker {ergebnis['id']} wurde gespeichert.",
        )

        self._load_techniker()

        item = str(ergebnis["id"])
        if self._techniker_tree.exists(item):
            self._techniker_tree.selection_set(item)
            self._techniker_tree.see(item)
            self._techniker_auswahl_laden()

    def _select_techniker(self):
        auswahl = self._techniker_tree.selection()

        if not auswahl:
            messagebox.showwarning(
                "Keine Auswahl",
                "Bitte zuerst einen Techniker auswählen.",
            )
            return

        techniker_id = self._techniker_daten[auswahl[0]]["id"]

        # Wartungsplan und durchgeführte Wartung
        for entry in (
            self._wp_techniker_id,
            self._w_techniker_id,
        ):
            entry.delete(0, tk.END)
            entry.insert(0, str(techniker_id))

        messagebox.showinfo(
            "Techniker übernommen",
            (
                f"Techniker-ID {techniker_id} wurde in "
                "Wartungsplan und Wartungsformular übernommen."
            ),
        )