import pandas as pd

from config import SCENARIO_NO_CONTROL, SCENARIOS


def calculate_metrics_by_building(results):
    """Calcula metricas por escenario y edificio."""
    ordered_results = results.sort_values(["scenario", "building", "hour"]).copy()
    metrics = (
        ordered_results.groupby(["scenario", "building"])
        .agg(
            consumption_total_kwh=("consumption", "sum"),
            pv_generation_total_kwh=("pv_generation", "sum"),
            pv_used_directly_kwh=("pv_used_directly", "sum"),
            battery_capacity_kwh=("battery_capacity", "first"),
            battery_initial_soc_kwh=("battery_initial_soc", "first"),
            battery_final_soc_kwh=("battery_soc", "last"),
            battery_min_soc_kwh=("battery_min_soc", "first"),
            battery_charge_input_total_kwh=("battery_charge_input", "sum"),
            battery_charge_total_kwh=("battery_charge", "sum"),
            battery_discharge_total_kwh=("battery_discharge", "sum"),
            battery_losses_total_kwh=("battery_losses", "sum"),
            grid_import_total_kwh=("grid_import", "sum"),
            grid_export_total_kwh=("grid_export", "sum"),
            peak_grid_import_kw=("grid_import", "max"),
            avg_battery_soc_kwh=("battery_soc", "mean"),
            energy_purchase_cost_eur=("energy_purchase_cost", "sum"),
            export_revenue_eur=("export_revenue", "sum"),
            energy_cost_eur=("energy_cost", "sum"),
        )
        .reset_index()
    )

    metrics["terminal_soc_difference_kwh"] = (
        metrics["battery_final_soc_kwh"] - metrics["battery_initial_soc_kwh"]
    )
    metrics = _add_self_consumption_metrics(metrics)
    return _order_by_scenario(metrics).round(2)


def calculate_global_metrics(results):
    """Calcula metricas agregadas por escenario desde los resultados horarios."""
    ordered_results = results.sort_values(["scenario", "building", "hour"]).copy()
    global_metrics = (
        ordered_results.groupby("scenario")
        .agg(
            consumption_total_kwh=("consumption", "sum"),
            pv_generation_total_kwh=("pv_generation", "sum"),
            pv_used_directly_kwh=("pv_used_directly", "sum"),
            battery_charge_input_total_kwh=("battery_charge_input", "sum"),
            battery_charge_total_kwh=("battery_charge", "sum"),
            battery_discharge_total_kwh=("battery_discharge", "sum"),
            battery_losses_total_kwh=("battery_losses", "sum"),
            grid_import_total_kwh=("grid_import", "sum"),
            grid_export_total_kwh=("grid_export", "sum"),
            energy_purchase_cost_eur=("energy_purchase_cost", "sum"),
            export_revenue_eur=("export_revenue", "sum"),
            energy_cost_eur=("energy_cost", "sum"),
        )
        .reset_index()
    )

    aggregate_peak = _calculate_aggregate_peak(ordered_results)
    aggregate_soc = _calculate_aggregate_soc(ordered_results)
    global_metrics = global_metrics.merge(aggregate_peak, on="scenario", how="left")
    global_metrics = global_metrics.merge(aggregate_soc, on="scenario", how="left")
    global_metrics["terminal_soc_difference_kwh"] = (
        global_metrics["battery_final_soc_kwh"] - global_metrics["battery_initial_soc_kwh"]
    )
    global_metrics = _add_self_consumption_metrics(global_metrics)
    global_metrics = _add_reduction_metrics(global_metrics)

    return _order_by_scenario(global_metrics).round(2)


def calculate_hourly_metrics_by_scenario(results):
    """Agrega las series horarias sumando los edificios por escenario y hora."""
    hourly = (
        results.groupby(["scenario", "hour"])
        .agg(
            consumption=("consumption", "sum"),
            pv_generation=("pv_generation", "sum"),
            grid_import=("grid_import", "sum"),
            grid_export=("grid_export", "sum"),
            battery_charge=("battery_charge", "sum"),
            battery_discharge=("battery_discharge", "sum"),
            battery_losses=("battery_losses", "sum"),
            battery_soc=("battery_soc", "sum"),
            energy_cost=("energy_cost", "sum"),
        )
        .reset_index()
    )
    return _order_by_scenario(hourly)


def _calculate_aggregate_peak(results):
    hourly_import = (
        results.groupby(["scenario", "hour"])["grid_import"]
        .sum()
        .reset_index(name="aggregate_grid_import")
    )
    return (
        hourly_import.groupby("scenario")["aggregate_grid_import"]
        .max()
        .reset_index(name="peak_grid_import_kw")
    )


def _calculate_aggregate_soc(results):
    building_soc = (
        results.groupby(["scenario", "building"])
        .agg(
            battery_capacity_kwh=("battery_capacity", "first"),
            battery_initial_soc_kwh=("battery_initial_soc", "first"),
            battery_final_soc_kwh=("battery_soc", "last"),
            battery_min_soc_kwh=("battery_min_soc", "first"),
        )
        .reset_index()
    )
    return (
        building_soc.groupby("scenario")
        .agg(
            battery_capacity_kwh=("battery_capacity_kwh", "sum"),
            battery_initial_soc_kwh=("battery_initial_soc_kwh", "sum"),
            battery_final_soc_kwh=("battery_final_soc_kwh", "sum"),
            battery_min_soc_kwh=("battery_min_soc_kwh", "sum"),
        )
        .reset_index()
    )


def _add_self_consumption_metrics(metrics):
    metrics = metrics.copy()
    metrics["pv_self_consumption_kwh"] = (
        metrics["pv_used_directly_kwh"] + metrics["battery_charge_input_total_kwh"]
    )
    metrics["pv_self_consumption_rate_pct"] = (
        metrics["pv_self_consumption_kwh"]
        / metrics["pv_generation_total_kwh"]
        * 100
    )
    return metrics


def _add_reduction_metrics(global_metrics):
    global_metrics = global_metrics.copy()
    baseline = global_metrics.loc[
        global_metrics["scenario"] == SCENARIO_NO_CONTROL
    ].iloc[0]

    global_metrics["grid_import_reduction_pct"] = _percent_reduction(
        baseline["grid_import_total_kwh"],
        global_metrics["grid_import_total_kwh"],
    )
    global_metrics["cost_reduction_pct"] = _percent_reduction(
        baseline["energy_cost_eur"],
        global_metrics["energy_cost_eur"],
    )
    global_metrics["peak_grid_import_reduction_pct"] = _percent_reduction(
        baseline["peak_grid_import_kw"],
        global_metrics["peak_grid_import_kw"],
    )
    return global_metrics


def _percent_reduction(baseline, values):
    if baseline == 0:
        return 0.0
    return (baseline - values) / baseline * 100


def _order_by_scenario(df):
    ordered = df.copy()
    ordered["scenario"] = pd.Categorical(
        ordered["scenario"],
        categories=SCENARIOS,
        ordered=True,
    )
    sort_columns = ["scenario"]
    if "hour" in ordered.columns:
        sort_columns.append("hour")
    if "building" in ordered.columns:
        sort_columns.append("building")

    ordered = ordered.sort_values(sort_columns).reset_index(drop=True)
    ordered["scenario"] = ordered["scenario"].astype(str)
    return ordered