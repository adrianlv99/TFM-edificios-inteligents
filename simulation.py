from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from building_agent import BuildingAgent
from config import (
    ADVANCED_PRICE_PERCENTILE,
    BASE_CONSUMPTION_SEEDS,
    BATTERY_CHARGE_EFFICIENCY,
    BATTERY_DISCHARGE_EFFICIENCY,
    BUILDING_NAMES,
    CSV_DECIMAL,
    CSV_ENCODING,
    CSV_SEPARATOR,
    DEFAULT_STUDY_CASE,
    EXPORT_PRICE_FACTOR,
    FIGURES_DIR,
    MAX_CYCLIC_DAYS,
    MIN_SOC_FRACTION,
    PEAK_CONSUMPTION_THRESHOLD,
    RESULTS_DIR,
    RULE_PRICE_THRESHOLD,
    SCENARIO_ADVANCED,
    SCENARIO_NO_CONTROL,
    SCENARIO_RULES,
    SCENARIOS,
    STUDY_CASES,
    TERMINAL_SOC_TOLERANCE,
)
from data_generator import generate_consumption_profile, generate_pv_profile, generate_price_profile
from metrics import calculate_global_metrics, calculate_metrics_by_building
from plots import plot_all


@dataclass(frozen=True)
class SimulationOutput:
    results: pd.DataFrame
    metrics_by_building: pd.DataFrame
    metrics_by_scenario: pd.DataFrame
    terminal_soc_test: pd.DataFrame
    price_profile: np.ndarray
    pv_profile: np.ndarray
    exported_files: dict[str, Path]
    study_case_name: str
    study_case_settings: dict


@dataclass(frozen=True)
class AllCasesOutput:
    results: pd.DataFrame
    metrics_by_building: pd.DataFrame
    metrics_by_scenario: pd.DataFrame
    terminal_soc_test: pd.DataFrame
    exported_files: dict[str, Path]


def create_buildings(study_case_settings=None):
    """Crea edificios con SOC inicial igual al SOC minimo tecnico."""
    settings = study_case_settings or STUDY_CASES[DEFAULT_STUDY_CASE]
    capacity_scale = settings["battery_capacity_scale"]
    power_scale = settings["battery_power_scale"]

    capacity_a = 10 * capacity_scale
    capacity_b = 8 * capacity_scale

    return [
        BuildingAgent(
            name="Edificio A",
            battery_capacity=capacity_a,
            initial_soc=capacity_a * MIN_SOC_FRACTION,
            max_charge_power=3 * power_scale,
            max_discharge_power=3 * power_scale,
            min_soc=MIN_SOC_FRACTION,
            charge_efficiency=BATTERY_CHARGE_EFFICIENCY,
            discharge_efficiency=BATTERY_DISCHARGE_EFFICIENCY,
            export_price_factor=EXPORT_PRICE_FACTOR,
        ),
        BuildingAgent(
            name="Edificio B",
            battery_capacity=capacity_b,
            initial_soc=capacity_b * MIN_SOC_FRACTION,
            max_charge_power=2.5 * power_scale,
            max_discharge_power=2.5 * power_scale,
            min_soc=MIN_SOC_FRACTION,
            charge_efficiency=BATTERY_CHARGE_EFFICIENCY,
            discharge_efficiency=BATTERY_DISCHARGE_EFFICIENCY,
            export_price_factor=EXPORT_PRICE_FACTOR,
        ),
    ]


def run_scenario(scenario_name, price_profile, pv_profile, study_case_name, study_case_settings):
    """Ejecuta un escenario completo para todos los edificios."""
    buildings = create_buildings(study_case_settings)
    results = []
    advanced_price_threshold = float(np.percentile(price_profile, ADVANCED_PRICE_PERCENTILE))

    for building in buildings:
        consumption_profile = generate_consumption_profile(
            seed=BASE_CONSUMPTION_SEEDS[building.name],
            scale=study_case_settings["consumption_scale"],
        )
        results.extend(
            _run_terminal_day(
                building=building,
                scenario_name=scenario_name,
                consumption_profile=consumption_profile,
                pv_profile=pv_profile,
                price_profile=price_profile,
                high_price_threshold=advanced_price_threshold,
                study_case_name=study_case_name,
            )
        )

    return pd.DataFrame(results)


def _run_terminal_day(
    building,
    scenario_name,
    consumption_profile,
    pv_profile,
    price_profile,
    high_price_threshold,
    study_case_name,
):
    for cycle_day in range(1, MAX_CYCLIC_DAYS + 1):
        day_initial_soc = building.soc
        building.initial_soc = day_initial_soc
        day_results = []

        for hour in range(24):
            if scenario_name == SCENARIO_NO_CONTROL:
                result = building.step_no_control(
                    hour=hour,
                    consumption=consumption_profile[hour],
                    pv_generation=pv_profile[hour],
                    price=price_profile[hour],
                )
            elif scenario_name == SCENARIO_RULES:
                result = building.step_rule_based(
                    hour=hour,
                    consumption=consumption_profile[hour],
                    pv_generation=pv_profile[hour],
                    price=price_profile[hour],
                    high_price_threshold=RULE_PRICE_THRESHOLD,
                    peak_consumption_threshold=PEAK_CONSUMPTION_THRESHOLD,
                )
            elif scenario_name == SCENARIO_ADVANCED:
                result = building.step_advanced_decision(
                    hour=hour,
                    consumption=consumption_profile[hour],
                    pv_generation=pv_profile[hour],
                    price=price_profile[hour],
                    high_price_threshold=high_price_threshold,
                    peak_consumption_threshold=PEAK_CONSUMPTION_THRESHOLD,
                )
            else:
                raise ValueError(f"Escenario no reconocido: {scenario_name}")

            result["study_case"] = study_case_name
            result["cycle_day"] = cycle_day
            day_results.append(result)

        terminal_difference = building.soc - day_initial_soc
        if abs(terminal_difference) <= TERMINAL_SOC_TOLERANCE:
            for result in day_results:
                result["terminal_soc_difference_day"] = terminal_difference
            return day_results

    raise RuntimeError(
        f"No se alcanzo igualdad terminal de SOC para {building.name}, "
        f"escenario {scenario_name}, caso {study_case_name}, "
        f"tras {MAX_CYCLIC_DAYS} dias repetidos."
    )


def run_simulation(
    export=True,
    print_summary=False,
    study_case_name=DEFAULT_STUDY_CASE,
):
    """Ejecuta escenarios, calcula metricas y devuelve todos los resultados."""
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)

    if study_case_name not in STUDY_CASES:
        valid_cases = ", ".join(STUDY_CASES)
        raise ValueError(f"Caso de estudio no reconocido: {study_case_name}. Validos: {valid_cases}")

    study_case_settings = STUDY_CASES[study_case_name]
    price_profile = generate_price_profile(scale=study_case_settings["price_scale"])
    pv_profile = generate_pv_profile(scale=study_case_settings["pv_scale"])
    all_results = []

    for scenario in SCENARIOS:
        all_results.append(
            run_scenario(
                scenario,
                price_profile,
                pv_profile,
                study_case_name,
                study_case_settings,
            )
        )

    results = pd.concat(all_results, ignore_index=True)
    metrics_by_building = calculate_metrics_by_building(results)
    metrics_by_scenario = calculate_global_metrics(results)
    metrics_by_building.insert(0, "study_case", study_case_name)
    metrics_by_scenario.insert(0, "study_case", study_case_name)
    terminal_soc_test = calculate_terminal_soc_equality(results, study_case_name)
    parameters = build_parameters_dataframe(study_case_name, study_case_settings)

    exported_files = {
        "Resultados horarios": RESULTS_DIR / "simulation_results_all_scenarios.csv",
        "Metricas por edificio": RESULTS_DIR / "metrics_by_building.csv",
        "Metricas por escenario": RESULTS_DIR / "metrics_by_scenario.csv",
        "Parametros simulacion": RESULTS_DIR / "simulation_parameters.csv",
        "Prueba SOC terminal": RESULTS_DIR / "terminal_soc_equality.csv",
        "Grafica energia y coste": FIGURES_DIR / "scenario_import_cost.png",
        "Grafica bateria": FIGURES_DIR / "scenario_battery_use.png",
        "Grafica reducciones": FIGURES_DIR / "scenario_reductions.png",
        "Grafica importacion horaria": FIGURES_DIR / "hourly_grid_import_by_scenario.png",
        "Grafica SOC horario": FIGURES_DIR / "hourly_battery_soc_by_scenario.png",
    }

    if export:
        export_dataframe(results, exported_files["Resultados horarios"])
        export_dataframe(metrics_by_building, exported_files["Metricas por edificio"])
        export_dataframe(metrics_by_scenario, exported_files["Metricas por escenario"])
        export_dataframe(parameters, exported_files["Parametros simulacion"])
        export_dataframe(terminal_soc_test, exported_files["Prueba SOC terminal"])
        plot_all(metrics_by_scenario, results)

    if print_summary:
        print("\nMetricas por edificio:")
        print(metrics_by_building)
        print("\nMetricas agregadas por escenario:")
        print(metrics_by_scenario)
        print("\nPrueba SOC terminal:")
        print(terminal_soc_test)
        print("\nParametros del caso:")
        print(parameters)

    return SimulationOutput(
        results=results,
        metrics_by_building=metrics_by_building,
        metrics_by_scenario=metrics_by_scenario,
        terminal_soc_test=terminal_soc_test,
        price_profile=price_profile,
        pv_profile=pv_profile,
        exported_files=exported_files,
        study_case_name=study_case_name,
        study_case_settings=study_case_settings,
    )


def run_all_study_cases(export=True, print_summary=False):
    """Ejecuta los seis casos y agrega resultados comparables."""
    outputs = [run_simulation(export=False, study_case_name=case) for case in STUDY_CASES]

    results = pd.concat([output.results for output in outputs], ignore_index=True)
    metrics_by_building = pd.concat([output.metrics_by_building for output in outputs], ignore_index=True)
    metrics_by_scenario = pd.concat([output.metrics_by_scenario for output in outputs], ignore_index=True)
    terminal_soc_test = pd.concat([output.terminal_soc_test for output in outputs], ignore_index=True)
    parameters = pd.concat(
        [build_parameters_dataframe(output.study_case_name, output.study_case_settings) for output in outputs],
        ignore_index=True,
    )

    exported_files = {
        "Resultados horarios todos los casos": RESULTS_DIR / "simulation_results_all_cases.csv",
        "Metricas por edificio todos los casos": RESULTS_DIR / "metrics_by_building_all_cases.csv",
        "Metricas por escenario todos los casos": RESULTS_DIR / "metrics_by_scenario_all_cases.csv",
        "Parametros todos los casos": RESULTS_DIR / "simulation_parameters_all_cases.csv",
        "Prueba SOC terminal todos los casos": RESULTS_DIR / "terminal_soc_equality_all_cases.csv",
    }

    if export:
        RESULTS_DIR.mkdir(exist_ok=True)
        export_dataframe(results, exported_files["Resultados horarios todos los casos"])
        export_dataframe(metrics_by_building, exported_files["Metricas por edificio todos los casos"])
        export_dataframe(metrics_by_scenario, exported_files["Metricas por escenario todos los casos"])
        export_dataframe(parameters, exported_files["Parametros todos los casos"])
        export_dataframe(terminal_soc_test, exported_files["Prueba SOC terminal todos los casos"])

    if print_summary:
        print("\nMetricas agregadas de todos los casos:")
        print(metrics_by_scenario)
        print("\nPrueba SOC terminal de todos los casos:")
        print(terminal_soc_test)

    return AllCasesOutput(
        results=results,
        metrics_by_building=metrics_by_building,
        metrics_by_scenario=metrics_by_scenario,
        terminal_soc_test=terminal_soc_test,
        exported_files=exported_files,
    )


def calculate_terminal_soc_equality(results, study_case_name):
    ordered = results.sort_values(["scenario", "building", "hour"]).copy()
    test = (
        ordered.groupby(["scenario", "building"])
        .agg(
            battery_initial_soc_kwh=("battery_initial_soc", "first"),
            battery_final_soc_kwh=("battery_soc", "last"),
            cycle_day=("cycle_day", "max"),
        )
        .reset_index()
    )
    test.insert(0, "study_case", study_case_name)
    test["terminal_soc_difference_kwh"] = (
        test["battery_final_soc_kwh"] - test["battery_initial_soc_kwh"]
    )
    test["tolerance_kwh"] = TERMINAL_SOC_TOLERANCE
    test["result"] = np.where(
        test["terminal_soc_difference_kwh"].abs() <= TERMINAL_SOC_TOLERANCE,
        "CUMPLE",
        "INCUMPLE",
    )
    return test.round(10)


def build_parameters_dataframe(study_case_name, study_case_settings):
    """Devuelve los parametros necesarios para reproducir la simulacion."""
    rows = []

    def add(section, parameter, value, description=""):
        rows.append({
            "section": section,
            "parameter": parameter,
            "value": value,
            "description": description,
        })

    add("caso", "study_case", study_case_name, STUDY_CASES[study_case_name]["description"])
    for key, value in study_case_settings.items():
        add("caso", key, value)

    for building_name in BUILDING_NAMES:
        add("semillas", f"seed_{building_name}", BASE_CONSUMPTION_SEEDS[building_name])

    add("umbrales", "rule_price_threshold_eur_kwh", RULE_PRICE_THRESHOLD)
    add("umbrales", "advanced_price_percentile", ADVANCED_PRICE_PERCENTILE)
    add("umbrales", "peak_consumption_threshold_kwh", PEAK_CONSUMPTION_THRESHOLD)
    add("bateria", "min_soc_fraction", MIN_SOC_FRACTION)
    add("bateria", "charge_efficiency", BATTERY_CHARGE_EFFICIENCY)
    add("bateria", "discharge_efficiency", BATTERY_DISCHARGE_EFFICIENCY)
    add("bateria", "terminal_soc_tolerance_kwh", TERMINAL_SOC_TOLERANCE)
    add("bateria", "max_cyclic_days", MAX_CYCLIC_DAYS)
    add("coste", "export_price_factor", EXPORT_PRICE_FACTOR)

    for building in create_buildings(study_case_settings):
        add(building.name, "battery_capacity_kwh", building.battery_capacity)
        add(building.name, "battery_initial_soc_kwh", building.initial_soc)
        add(building.name, "battery_initial_soc_pct", building.initial_soc / building.battery_capacity * 100)
        add(building.name, "battery_min_soc_pct", building.min_soc * 100)
        add(building.name, "max_charge_power_kw", building.max_charge_power)
        add(building.name, "max_discharge_power_kw", building.max_discharge_power)

    return pd.DataFrame(rows)


def export_dataframe(df, path):
    """Exporta CSV compatible con Excel en configuracion regional espanola."""
    try:
        df.to_csv(
            path,
            index=False,
            sep=CSV_SEPARATOR,
            decimal=CSV_DECIMAL,
            encoding=CSV_ENCODING,
        )
        return path
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
        df.to_csv(
            fallback,
            index=False,
            sep=CSV_SEPARATOR,
            decimal=CSV_DECIMAL,
            encoding=CSV_ENCODING,
        )
        print(f"Aviso: {path} estaba bloqueado. Se ha escrito {fallback}.")
        return fallback