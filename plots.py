import matplotlib.pyplot as plt
import numpy as np

from config import FIGURES_DIR, SCENARIOS
from metrics import calculate_hourly_metrics_by_scenario


def plot_global_metrics(global_metrics):
    """Genera graficas comparativas agregadas de los escenarios."""
    FIGURES_DIR.mkdir(exist_ok=True)
    ordered = _order_by_scenario(global_metrics)

    _plot_import_cost(ordered)
    _plot_battery_use(ordered)
    _plot_reductions(ordered)


def plot_hourly_metrics(results):
    """Genera graficas horarias que ayudan a interpretar la flexibilidad."""
    FIGURES_DIR.mkdir(exist_ok=True)
    hourly = calculate_hourly_metrics_by_scenario(results)

    _plot_hourly_grid_import(hourly)
    _plot_hourly_battery_soc(hourly)


def plot_all(global_metrics, results):
    plot_global_metrics(global_metrics)
    plot_hourly_metrics(results)


def _plot_import_cost(ordered):
    x = np.arange(len(ordered))
    fig, ax1 = plt.subplots(figsize=(9, 5))

    ax1.bar(
        x - 0.18,
        ordered["grid_import_total_kwh"],
        width=0.36,
        label="Energia importada (kWh)",
        color="#2563eb",
    )
    ax1.set_ylabel("kWh")
    ax1.set_xticks(x)
    ax1.set_xticklabels(ordered["scenario"], rotation=8, ha="right")
    ax1.grid(axis="y", alpha=0.25)

    ax2 = ax1.twinx()
    ax2.plot(
        x,
        ordered["energy_cost_eur"],
        marker="o",
        linewidth=2,
        label="Coste neto (EUR)",
        color="#dc2626",
    )
    ax2.set_ylabel("EUR")

    ax1.set_title("Energia importada y coste neto por escenario")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "scenario_import_cost.png", dpi=300)
    plt.close(fig)


def _plot_battery_use(ordered):
    battery_use = ordered[[
        "scenario",
        "battery_charge_input_total_kwh",
        "battery_charge_total_kwh",
        "battery_discharge_total_kwh",
        "battery_losses_total_kwh",
    ]].rename(columns={
        "scenario": "Escenario",
        "battery_charge_input_total_kwh": "PV enviada a bateria (kWh)",
        "battery_charge_total_kwh": "Energia almacenada (kWh)",
        "battery_discharge_total_kwh": "Energia entregada (kWh)",
        "battery_losses_total_kwh": "Perdidas bateria (kWh)",
    })

    ax = battery_use.set_index("Escenario").plot(kind="bar", figsize=(10, 5))
    ax.set_title("Uso agregado de bateria por escenario")
    ax.set_xlabel("Escenario")
    ax.set_ylabel("Energia (kWh)")
    ax.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=8, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "scenario_battery_use.png", dpi=300)
    plt.close()


def _plot_reductions(ordered):
    reductions = ordered[[
        "scenario",
        "grid_import_reduction_pct",
        "cost_reduction_pct",
        "peak_grid_import_reduction_pct",
    ]].rename(columns={
        "scenario": "Escenario",
        "grid_import_reduction_pct": "Reduccion energia importada (%)",
        "cost_reduction_pct": "Reduccion coste neto (%)",
        "peak_grid_import_reduction_pct": "Reduccion pico agregado (%)",
    })

    ax = reductions.set_index("Escenario").plot(kind="bar", figsize=(10, 5))
    ax.set_title("Reduccion frente al escenario sin control")
    ax.set_xlabel("Escenario")
    ax.set_ylabel("Reduccion (%)")
    ax.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=8, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "scenario_reductions.png", dpi=300)
    plt.close()


def _plot_hourly_grid_import(hourly):
    fig, ax = plt.subplots(figsize=(10, 5))

    for scenario in SCENARIOS:
        subset = hourly[hourly["scenario"] == scenario].sort_values("hour")
        ax.plot(
            subset["hour"],
            subset["grid_import"],
            marker="o",
            linewidth=2,
            label=scenario,
        )

    ax.set_title("Importacion agregada de red por hora")
    ax.set_xlabel("Hora")
    ax.set_ylabel("kWh")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "hourly_grid_import_by_scenario.png", dpi=300)
    plt.close(fig)


def _plot_hourly_battery_soc(hourly):
    fig, ax = plt.subplots(figsize=(10, 5))

    for scenario in SCENARIOS:
        subset = hourly[hourly["scenario"] == scenario].sort_values("hour")
        ax.plot(
            subset["hour"],
            subset["battery_soc"],
            marker="o",
            linewidth=2,
            label=scenario,
        )

    ax.set_title("Estado de carga agregado de bateria por hora")
    ax.set_xlabel("Hora")
    ax.set_ylabel("SOC agregado (kWh)")
    ax.set_xticks(range(0, 24, 2))
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "hourly_battery_soc_by_scenario.png", dpi=300)
    plt.close(fig)


def _order_by_scenario(df):
    return df.set_index("scenario").loc[SCENARIOS].reset_index()
