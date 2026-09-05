import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import numpy as np
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from config import (
    BUILDING_NAMES,
    DEFAULT_STUDY_CASE,
    SCENARIO_ADVANCED,
    SCENARIOS,
    STUDY_CASES,
)
from simulation import run_simulation


GLOBAL_COLUMNS = [
    "scenario",
    "consumption_total_kwh",
    "pv_generation_total_kwh",
    "pv_self_consumption_rate_pct",
    "grid_import_total_kwh",
    "grid_export_total_kwh",
    "peak_grid_import_kw",
    "battery_capacity_kwh",
    "battery_initial_soc_kwh",
    "battery_final_soc_kwh",
    "terminal_soc_difference_kwh",
    "battery_charge_total_kwh",
    "battery_discharge_total_kwh",
    "battery_losses_total_kwh",
    "energy_purchase_cost_eur",
    "export_revenue_eur",
    "energy_cost_eur",
    "grid_import_reduction_pct",
    "peak_grid_import_reduction_pct",
    "cost_reduction_pct",
]

BUILDING_COLUMNS = [
    "scenario",
    "building",
    "consumption_total_kwh",
    "pv_generation_total_kwh",
    "pv_self_consumption_rate_pct",
    "grid_import_total_kwh",
    "grid_export_total_kwh",
    "battery_capacity_kwh",
    "battery_initial_soc_kwh",
    "battery_final_soc_kwh",
    "terminal_soc_difference_kwh",
    "battery_charge_total_kwh",
    "battery_discharge_total_kwh",
    "battery_losses_total_kwh",
    "avg_battery_soc_kwh",
    "energy_purchase_cost_eur",
    "export_revenue_eur",
    "energy_cost_eur",
]

HOURLY_COLUMNS = [
    "hour",
    "consumption",
    "pv_generation",
    "price",
    "export_price",
    "battery_soc",
    "battery_charge_input",
    "battery_charge",
    "battery_discharge",
    "battery_losses",
    "grid_import",
    "grid_export",
    "energy_purchase_cost",
    "export_revenue",
    "energy_cost",
    "decision",
]

COLUMN_LABELS = {
    "scenario": "Escenario",
    "building": "Edificio",
    "hour": "Hora",
    "consumption": "Consumo kWh",
    "consumption_total_kwh": "Consumo kWh",
    "pv_generation": "PV kWh",
    "pv_generation_total_kwh": "PV kWh",
    "pv_used_directly": "PV directa kWh",
    "pv_used_directly_kwh": "PV directa kWh",
    "price": "Compra EUR/kWh",
    "export_price": "Venta EUR/kWh",
    "battery_soc": "SOC kWh",
    "battery_capacity_kwh": "Capacidad bat. kWh",
    "battery_initial_soc_kwh": "SOC inicial kWh",
    "battery_final_soc_kwh": "SOC final kWh",
    "terminal_soc_difference_kwh": "Diferencia SOC kWh",
    "battery_min_soc_kwh": "SOC minimo kWh",
    "avg_battery_soc_kwh": "SOC medio kWh",
    "battery_charge_input": "PV a bat. kWh",
    "battery_charge_input_total_kwh": "PV a bat. kWh",
    "battery_charge": "Carga almacenada kWh",
    "battery_charge_total_kwh": "Carga almacenada kWh",
    "battery_discharge": "Descarga bat. kWh",
    "battery_discharge_total_kwh": "Descarga bat. kWh",
    "battery_losses": "Perdidas bat. kWh",
    "battery_losses_total_kwh": "Perdidas bat. kWh",
    "grid_import": "Importacion kWh",
    "grid_import_total_kwh": "Importacion kWh",
    "grid_export": "Exportacion kWh",
    "grid_export_total_kwh": "Exportacion kWh",
    "peak_grid_import_kw": "Pico red kW",
    "energy_purchase_cost": "Coste compra EUR",
    "energy_purchase_cost_eur": "Coste compra EUR",
    "export_revenue": "Compensacion EUR",
    "export_revenue_eur": "Compensacion EUR",
    "energy_cost": "Coste neto EUR",
    "energy_cost_eur": "Coste neto EUR",
    "pv_self_consumption_kwh": "Autoconsumo kWh",
    "pv_self_consumption_rate_pct": "Autoconsumo %",
    "grid_import_reduction_pct": "Reduccion red %",
    "peak_grid_import_reduction_pct": "Reduccion pico %",
    "cost_reduction_pct": "Reduccion coste %",
    "decision": "Decision",
}

COLUMN_WIDTHS = {
    "scenario": 140,
    "building": 100,
    "hour": 60,
    "decision": 360,
}


class SimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de edificios inteligentes")
        self.geometry("1320x840")
        self.minsize(1100, 720)

        self.output = None
        self.run_count = 0
        self.status_var = tk.StringVar(value="Preparado")
        self.scenario_var = tk.StringVar(value=SCENARIOS[-1])
        self.building_var = tk.StringVar(value=BUILDING_NAMES[0])
        self.case_var = tk.StringVar(value=DEFAULT_STUDY_CASE)
        self.case_info_var = tk.StringVar(value=STUDY_CASES[DEFAULT_STUDY_CASE]["description"])

        self._configure_style()
        self._build_layout()
        self.execute_simulation()

    def _configure_style(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.colors = {
            "bg": "#f4f7fb",
            "panel": "#ffffff",
            "text": "#172033",
            "muted": "#526173",
            "border": "#d8e0ea",
            "header": "#123247",
            "accent": "#0f766e",
            "blue": "#2563eb",
            "green": "#16a34a",
            "amber": "#d97706",
            "red": "#dc2626",
            "purple": "#7c3aed",
        }

        self.configure(bg=self.colors["bg"])
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Panel.TFrame", background=self.colors["panel"])
        self.style.configure("Header.TFrame", background=self.colors["header"])
        self.style.configure(
            "HeaderTitle.TLabel",
            background=self.colors["header"],
            foreground="#ffffff",
            font=("Segoe UI", 17, "bold"),
        )
        self.style.configure(
            "HeaderText.TLabel",
            background=self.colors["header"],
            foreground="#dbeafe",
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Muted.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 9),
        )
        self.style.configure("TLabelframe", background=self.colors["bg"])
        self.style.configure(
            "TLabelframe.Label",
            background=self.colors["bg"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10, "bold"),
        )
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        self.style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=(14, 8))

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=14, pady=(12, 8))

        self._build_summary_tab()
        self._build_charts_tab()
        self._build_hourly_tab()
        self._build_profiles_tab()
        self._build_files_tab()

        status = ttk.Label(
            self,
            textvariable=self.status_var,
            style="Muted.TLabel",
            anchor="w",
            padding=(14, 5),
        )
        status.grid(row=2, column=0, sticky="ew")

    def _build_header(self):
        header = ttk.Frame(self, style="Header.TFrame", padding=(18, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(
            header,
            text="Simulador multiagente de edificios inteligentes",
            style="HeaderTitle.TLabel",
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(
            header,
            text="Comparativa visual de escenarios, baterias, PV, costes netos y decisiones horarias",
            style="HeaderText.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        case_info = ttk.Label(
            header,
            textvariable=self.case_info_var,
            style="HeaderText.TLabel",
        )
        case_info.grid(row=2, column=0, sticky="w", pady=(4, 0))

        actions = ttk.Frame(header, style="Header.TFrame")
        actions.grid(row=0, column=1, rowspan=3, sticky="e")

        ttk.Label(actions, text="Caso", style="HeaderText.TLabel").grid(
            row=0,
            column=0,
            sticky="e",
            padx=(0, 6),
        )
        case_box = ttk.Combobox(
            actions,
            textvariable=self.case_var,
            values=list(STUDY_CASES.keys()),
            state="readonly",
            width=22,
        )
        case_box.grid(row=0, column=1, sticky="e", padx=(0, 8))
        case_box.bind("<<ComboboxSelected>>", lambda _event: self.update_case_info())

        ttk.Button(
            actions,
            text="Ejecutar simulacion",
            style="Accent.TButton",
            command=self.execute_simulation,
        ).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(
            actions,
            text="Abrir resultados",
            command=self.open_results_folder,
        ).grid(row=0, column=3, padx=(0, 8))
        ttk.Button(actions, text="Salir", command=self.destroy).grid(row=0, column=4)

    def _build_summary_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        self.notebook.add(tab, text="Resumen")

        self.kpi_frame = ttk.Frame(tab)
        self.kpi_frame.grid(row=0, column=0, sticky="ew")

        global_frame = ttk.LabelFrame(tab, text="Metricas agregadas por escenario", padding=10)
        global_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 8))
        global_frame.columnconfigure(0, weight=1)
        global_frame.rowconfigure(0, weight=1)
        self.global_table = self._create_table(global_frame, height=6)
        self.global_table["container"].grid(row=0, column=0, sticky="nsew")

        building_frame = ttk.LabelFrame(tab, text="Metricas por edificio", padding=10)
        building_frame.grid(row=2, column=0, sticky="nsew")
        building_frame.columnconfigure(0, weight=1)
        building_frame.rowconfigure(0, weight=1)
        self.building_table = self._create_table(building_frame, height=9)
        self.building_table["container"].grid(row=0, column=0, sticky="nsew")

    def _build_charts_tab(self):
        tab = ttk.Frame(self.notebook, padding=8)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        self.notebook.add(tab, text="Graficas")

        self.global_figure = Figure(figsize=(11, 7), dpi=100)
        self.global_canvas = FigureCanvasTkAgg(self.global_figure, master=tab)
        self.global_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        toolbar_frame = ttk.Frame(tab)
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        NavigationToolbar2Tk(self.global_canvas, toolbar_frame, pack_toolbar=False).grid(
            row=0,
            column=0,
            sticky="w",
        )

    def _build_hourly_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)
        self.notebook.add(tab, text="Detalle horario")

        filters = ttk.Frame(tab)
        filters.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        filters.columnconfigure(5, weight=1)

        ttk.Label(filters, text="Escenario").grid(row=0, column=0, sticky="w")
        scenario_box = ttk.Combobox(
            filters,
            textvariable=self.scenario_var,
            values=SCENARIOS,
            state="readonly",
            width=22,
        )
        scenario_box.grid(row=0, column=1, sticky="w", padx=(8, 20))
        scenario_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_hourly_tab())

        ttk.Label(filters, text="Edificio").grid(row=0, column=2, sticky="w")
        building_box = ttk.Combobox(
            filters,
            textvariable=self.building_var,
            values=BUILDING_NAMES,
            state="readonly",
            width=14,
        )
        building_box.grid(row=0, column=3, sticky="w", padx=(8, 20))
        building_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_hourly_tab())

        ttk.Button(
            filters,
            text="Actualizar vista",
            command=self.refresh_hourly_tab,
        ).grid(row=0, column=4, sticky="w")

        chart_frame = ttk.LabelFrame(tab, text="Evolucion horaria", padding=8)
        chart_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)

        self.hourly_figure = Figure(figsize=(11, 3.4), dpi=100)
        self.hourly_canvas = FigureCanvasTkAgg(self.hourly_figure, master=chart_frame)
        self.hourly_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        table_frame = ttk.LabelFrame(tab, text="Resultados horarios y decision", padding=8)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.hourly_table = self._create_table(table_frame, height=11)
        self.hourly_table["container"].grid(row=0, column=0, sticky="nsew")

    def _build_profiles_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        self.notebook.add(tab, text="Perfiles entrada")

        profile_chart = ttk.LabelFrame(tab, text="PV, precio y consumo de referencia", padding=8)
        profile_chart.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        profile_chart.columnconfigure(0, weight=1)
        profile_chart.rowconfigure(0, weight=1)

        self.profile_figure = Figure(figsize=(11, 3.5), dpi=100)
        self.profile_canvas = FigureCanvasTkAgg(self.profile_figure, master=profile_chart)
        self.profile_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        profile_table_frame = ttk.LabelFrame(tab, text="Datos horarios de entrada", padding=8)
        profile_table_frame.grid(row=1, column=0, sticky="nsew")
        profile_table_frame.columnconfigure(0, weight=1)
        profile_table_frame.rowconfigure(0, weight=1)
        self.profile_table = self._create_table(profile_table_frame, height=10)
        self.profile_table["container"].grid(row=0, column=0, sticky="nsew")

    def _build_files_tab(self):
        tab = ttk.Frame(self.notebook, padding=12)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        self.notebook.add(tab, text="Archivos")

        frame = ttk.LabelFrame(tab, text="CSV e imagenes generadas", padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.files_table = self._create_table(frame, height=12)
        self.files_table["container"].grid(row=0, column=0, sticky="nsew")

        actions = ttk.Frame(frame)
        actions.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(actions, text="Abrir seleccionado", command=self.open_selected_file).grid(
            row=0,
            column=0,
            padx=(0, 8),
        )
        ttk.Button(actions, text="Abrir carpeta results", command=self.open_results_folder).grid(
            row=0,
            column=1,
            padx=(0, 8),
        )
        ttk.Button(actions, text="Refrescar lista", command=self.refresh_files_tab).grid(
            row=0,
            column=2,
        )

    def _create_table(self, parent, height):
        container = ttk.Frame(parent)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        tree = ttk.Treeview(container, show="headings", height=height)
        vertical = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")

        return {"container": container, "tree": tree}

    def execute_simulation(self):
        case_name = self.case_var.get()
        self.status_var.set(f"Ejecutando simulacion del caso: {case_name}...")
        self.update_idletasks()

        try:
            self.output = run_simulation(
                export=True,
                print_summary=False,
                study_case_name=case_name,
            )
        except Exception as exc:
            self.status_var.set("Error al ejecutar la simulacion")
            messagebox.showerror("Error de simulacion", str(exc))
            return

        self.refresh_all()
        self.run_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(
            f"Simulacion {self.run_count} completada a las {timestamp}. "
            f"Caso: {case_name}. Resultados actualizados."
        )

    def update_case_info(self):
        case_name = self.case_var.get()
        self.case_info_var.set(STUDY_CASES[case_name]["description"])

    def refresh_all(self):
        if self.output is None:
            return

        self.refresh_summary_tab()
        self.refresh_global_charts()
        self.refresh_hourly_tab()
        self.refresh_profiles_tab()
        self.refresh_files_tab()

    def refresh_summary_tab(self):
        metrics = self.output.metrics_by_scenario.copy()
        building_metrics = self.output.metrics_by_building.copy()

        self._render_kpis(metrics)
        self._fill_table(self.global_table["tree"], metrics, GLOBAL_COLUMNS)
        self._fill_table(self.building_table["tree"], building_metrics, BUILDING_COLUMNS)

    def _render_kpis(self, metrics):
        for child in self.kpi_frame.winfo_children():
            child.destroy()

        best_cost = metrics.loc[metrics["energy_cost_eur"].idxmin()]
        best_import = metrics.loc[metrics["grid_import_total_kwh"].idxmin()]
        advanced_row = metrics.loc[metrics["scenario"] == SCENARIO_ADVANCED].iloc[0]

        kpis = [
            (
                "Menor coste",
                str(best_cost["scenario"]),
                f"{best_cost['energy_cost_eur']:.2f} EUR",
                self.colors["green"],
            ),
            (
                "Menor importacion de red",
                str(best_import["scenario"]),
                f"{best_import['grid_import_total_kwh']:.2f} kWh",
                self.colors["blue"],
            ),
            (
                "Ahorro coste avanzado",
                SCENARIO_ADVANCED,
                f"{advanced_row['cost_reduction_pct']:.2f} %",
                self.colors["purple"],
            ),
            (
                "Reduccion pico avanzado",
                SCENARIO_ADVANCED,
                f"{advanced_row['peak_grid_import_reduction_pct']:.2f} %",
                self.colors["amber"],
            ),
        ]

        for index, (title, subtitle, value, accent) in enumerate(kpis):
            card = tk.Frame(
                self.kpi_frame,
                bg=self.colors["panel"],
                highlightbackground=self.colors["border"],
                highlightthickness=1,
            )
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 10, 0))
            self.kpi_frame.columnconfigure(index, weight=1)

            accent_bar = tk.Frame(card, bg=accent, width=5)
            accent_bar.pack(side="left", fill="y")

            body = tk.Frame(card, bg=self.colors["panel"], padx=14, pady=10)
            body.pack(side="left", fill="both", expand=True)
            tk.Label(
                body,
                text=title,
                bg=self.colors["panel"],
                fg=self.colors["muted"],
                font=("Segoe UI", 9),
                anchor="w",
            ).pack(fill="x")
            tk.Label(
                body,
                text=value,
                bg=self.colors["panel"],
                fg=self.colors["text"],
                font=("Segoe UI", 18, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(2, 0))
            tk.Label(
                body,
                text=subtitle,
                bg=self.colors["panel"],
                fg=self.colors["muted"],
                font=("Segoe UI", 9),
                anchor="w",
            ).pack(fill="x", pady=(2, 0))

    def refresh_global_charts(self):
        metrics = self.output.metrics_by_scenario.copy()
        scenario_labels = list(metrics["scenario"])
        x = np.arange(len(scenario_labels))

        self.global_figure.clear()
        self.global_figure.subplots_adjust(hspace=0.42, wspace=0.34)

        ax1 = self.global_figure.add_subplot(2, 2, 1)
        ax1.bar(
            x - 0.18,
            metrics["grid_import_total_kwh"],
            width=0.36,
            label="Importacion kWh",
            color=self.colors["blue"],
        )
        ax1.set_title("Energia importada y coste")
        ax1.set_xticks(x)
        ax1.set_xticklabels(scenario_labels, rotation=10, ha="right")
        ax1.set_ylabel("kWh")
        ax1.grid(axis="y", alpha=0.25)
        ax1b = ax1.twinx()
        ax1b.plot(
            x,
            metrics["energy_cost_eur"],
            marker="o",
            linewidth=2,
            color=self.colors["red"],
            label="Coste neto EUR",
        )
        ax1b.set_ylabel("EUR")

        ax2 = self.global_figure.add_subplot(2, 2, 2)
        ax2.bar(
            x - 0.26,
            metrics["grid_import_reduction_pct"],
            width=0.26,
            label="Reduccion red",
            color=self.colors["green"],
        )
        ax2.bar(
            x,
            metrics["peak_grid_import_reduction_pct"],
            width=0.26,
            label="Reduccion pico",
            color=self.colors["blue"],
        )
        ax2.bar(
            x + 0.26,
            metrics["cost_reduction_pct"],
            width=0.26,
            label="Reduccion coste neto",
            color=self.colors["amber"],
        )
        ax2.set_title("Reducciones frente al caso base")
        ax2.set_xticks(x)
        ax2.set_xticklabels(scenario_labels, rotation=10, ha="right")
        ax2.set_ylabel("%")
        ax2.legend(loc="upper left", fontsize=8)
        ax2.grid(axis="y", alpha=0.25)

        ax3 = self.global_figure.add_subplot(2, 2, 3)
        ax3.bar(
            x - 0.26,
            metrics["battery_charge_total_kwh"],
            width=0.26,
            label="Carga almacenada",
            color=self.colors["accent"],
        )
        ax3.bar(
            x,
            metrics["battery_discharge_total_kwh"],
            width=0.26,
            label="Descarga",
            color=self.colors["purple"],
        )
        ax3.bar(
            x + 0.26,
            metrics["battery_losses_total_kwh"],
            width=0.26,
            label="Perdidas",
            color=self.colors["amber"],
        )
        ax3.set_title("Uso agregado de bateria")
        ax3.set_xticks(x)
        ax3.set_xticklabels(scenario_labels, rotation=10, ha="right")
        ax3.set_ylabel("kWh")
        ax3.legend(loc="upper left", fontsize=8)
        ax3.grid(axis="y", alpha=0.25)

        ax4 = self.global_figure.add_subplot(2, 2, 4)
        ax4.bar(
            x - 0.18,
            metrics["pv_self_consumption_rate_pct"],
            width=0.36,
            label="Autoconsumo PV",
            color=self.colors["green"],
        )
        ax4.bar(
            x + 0.18,
            metrics["grid_export_total_kwh"],
            width=0.36,
            label="Exportacion kWh",
            color=self.colors["blue"],
        )
        ax4.set_title("Aprovechamiento fotovoltaico")
        ax4.set_xticks(x)
        ax4.set_xticklabels(scenario_labels, rotation=10, ha="right")
        ax4.set_ylabel("% / kWh")
        ax4.legend(loc="upper left", fontsize=8)
        ax4.grid(axis="y", alpha=0.25)

        self.global_canvas.draw_idle()

    def refresh_hourly_tab(self):
        if self.output is None:
            return

        scenario = self.scenario_var.get()
        building = self.building_var.get()
        subset = self.output.results[
            (self.output.results["scenario"] == scenario)
            & (self.output.results["building"] == building)
        ].sort_values("hour")

        self._fill_table(self.hourly_table["tree"], subset, HOURLY_COLUMNS)
        self._draw_hourly_chart(subset, scenario, building)

    def _draw_hourly_chart(self, subset, scenario, building):
        self.hourly_figure.clear()
        ax = self.hourly_figure.add_subplot(1, 1, 1)

        hours = subset["hour"]
        ax.plot(hours, subset["consumption"], label="Consumo", color=self.colors["red"], linewidth=2)
        ax.plot(hours, subset["pv_generation"], label="PV", color=self.colors["green"], linewidth=2)
        ax.plot(hours, subset["grid_import"], label="Importacion red", color=self.colors["blue"], linewidth=2)
        ax.plot(hours, subset["battery_soc"], label="SOC bateria", color=self.colors["purple"], linewidth=2)
        ax.bar(
            hours,
            subset["battery_charge"],
            width=0.35,
            label="Carga bat.",
            color=self.colors["accent"],
            alpha=0.35,
        )
        ax.bar(
            hours,
            -subset["battery_discharge"],
            width=0.35,
            label="Descarga bat.",
            color=self.colors["amber"],
            alpha=0.35,
        )
        ax.set_title(f"{scenario} - {building}")
        ax.set_xlabel("Hora")
        ax.set_ylabel("kWh")
        ax.set_xticks(range(0, 24, 2))
        ax.grid(axis="y", alpha=0.25)

        ax2 = ax.twinx()
        ax2.plot(hours, subset["price"], label="Precio", color="#111827", linestyle="--", linewidth=1.6)
        ax2.set_ylabel("EUR/kWh")

        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc="upper left", fontsize=8, ncol=3)

        self.hourly_figure.tight_layout()
        self.hourly_canvas.draw_idle()

    def refresh_profiles_tab(self):
        profile_df = self._build_profile_dataframe()
        self._fill_table(
            self.profile_table["tree"],
            profile_df,
            ["hour", "price", "pv_generation", "consumption_Edificio A", "consumption_Edificio B"],
            labels={
                "consumption_Edificio A": "Consumo Edificio A",
                "consumption_Edificio B": "Consumo Edificio B",
            },
        )
        self._draw_profiles_chart(profile_df)

    def _build_profile_dataframe(self):
        base = self.output.results[self.output.results["scenario"] == "Sin control"].copy()
        pivot = base.pivot_table(
            index="hour",
            columns="building",
            values="consumption",
            aggfunc="first",
        ).reset_index()
        pivot.columns.name = None
        pivot = pivot.rename(columns={
            "Edificio A": "consumption_Edificio A",
            "Edificio B": "consumption_Edificio B",
        })
        pivot["price"] = self.output.price_profile
        pivot["pv_generation"] = self.output.pv_profile
        return pivot[[
            "hour",
            "price",
            "pv_generation",
            "consumption_Edificio A",
            "consumption_Edificio B",
        ]]

    def _draw_profiles_chart(self, profile_df):
        self.profile_figure.clear()
        ax = self.profile_figure.add_subplot(1, 1, 1)
        hours = profile_df["hour"]

        ax.plot(
            hours,
            profile_df["pv_generation"],
            label="PV",
            color=self.colors["green"],
            linewidth=2,
        )
        ax.plot(
            hours,
            profile_df["consumption_Edificio A"],
            label="Consumo A",
            color=self.colors["blue"],
            linewidth=2,
        )
        ax.plot(
            hours,
            profile_df["consumption_Edificio B"],
            label="Consumo B",
            color=self.colors["amber"],
            linewidth=2,
        )
        ax.set_xlabel("Hora")
        ax.set_ylabel("kWh")
        ax.set_xticks(range(0, 24, 2))
        ax.grid(axis="y", alpha=0.25)

        ax2 = ax.twinx()
        ax2.plot(
            hours,
            profile_df["price"],
            label="Precio",
            color="#111827",
            linestyle="--",
            linewidth=1.6,
        )
        ax2.set_ylabel("EUR/kWh")

        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc="upper left", fontsize=8, ncol=4)
        ax.set_title("Perfiles sinteticos usados en la simulacion")

        self.profile_figure.tight_layout()
        self.profile_canvas.draw_idle()

    def refresh_files_tab(self):
        if self.output is None:
            return

        rows = []
        for description, path in self.output.exported_files.items():
            resolved = Path(path)
            rows.append({
                "description": description,
                "status": "Generado" if resolved.exists() else "Pendiente",
                "path": str(resolved),
            })

        df = pd.DataFrame(rows)
        self._fill_table(
            self.files_table["tree"],
            df,
            ["description", "status", "path"],
            labels={
                "description": "Archivo",
                "status": "Estado",
                "path": "Ruta",
            },
        )

    def open_selected_file(self):
        selection = self.files_table["tree"].selection()
        if not selection:
            messagebox.showinfo("Seleccion requerida", "Selecciona un archivo de la tabla.")
            return

        values = self.files_table["tree"].item(selection[0], "values")
        path = Path(values[2])
        self._open_path(path)

    def open_results_folder(self):
        self._open_path(Path("results"))

    def _open_path(self, path):
        resolved = Path(path).resolve()
        if not resolved.exists():
            messagebox.showwarning("No encontrado", f"No existe: {resolved}")
            return

        try:
            if os.name == "nt":
                os.startfile(resolved)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(resolved)], check=False)
            else:
                subprocess.run(["xdg-open", str(resolved)], check=False)
        except OSError as exc:
            messagebox.showerror("No se pudo abrir", str(exc))

    def _fill_table(self, tree, df, columns, labels=None):
        labels = labels or {}
        all_labels = {**COLUMN_LABELS, **labels}
        tree.delete(*tree.get_children())
        tree["columns"] = columns

        for column in columns:
            tree.heading(column, text=all_labels.get(column, column), anchor="w")
            width = COLUMN_WIDTHS.get(column, 118)
            if column == "path":
                width = 520
            tree.column(column, width=width, minwidth=60, anchor="w", stretch=column in {"decision", "path"})

        for _, row in df.iterrows():
            values = [self._format_value(row[column]) for column in columns]
            tree.insert("", "end", values=values)

    def _format_value(self, value):
        if pd.isna(value):
            return ""
        if isinstance(value, (float, np.floating)):
            return f"{value:.2f}"
        if isinstance(value, (int, np.integer)):
            return str(value)
        return str(value)


def launch_gui():
    app = SimulatorGUI()
    app.mainloop()
