from pathlib import Path


RESULTS_DIR = Path("results")
FIGURES_DIR = Path("figures")

SCENARIO_NO_CONTROL = "Sin control"
SCENARIO_RULES = "Reglas"
SCENARIO_ADVANCED = "Reglas + decision avanzada"
SCENARIOS = [SCENARIO_NO_CONTROL, SCENARIO_RULES, SCENARIO_ADVANCED]

BUILDING_NAMES = ["Edificio A", "Edificio B"]
BASE_CONSUMPTION_SEEDS = {
    "Edificio A": 1,
    "Edificio B": 2,
}

DEFAULT_STUDY_CASE = "Caso base"
STUDY_CASES = {
    "Caso base": {
        "description": "Perfiles sinteticos originales.",
        "consumption_scale": 1.00,
        "pv_scale": 1.00,
        "price_scale": 1.00,
        "battery_capacity_scale": 1.00,
        "battery_power_scale": 1.00,
    },
    "Alta demanda": {
        "description": "Aumenta el consumo un 20 % para simular mayor actividad del edificio.",
        "consumption_scale": 1.20,
        "pv_scale": 1.00,
        "price_scale": 1.00,
        "battery_capacity_scale": 1.00,
        "battery_power_scale": 1.00,
    },
    "Baja irradiacion": {
        "description": "Reduce la generacion fotovoltaica un 35 %.",
        "consumption_scale": 1.00,
        "pv_scale": 0.65,
        "price_scale": 1.00,
        "battery_capacity_scale": 1.00,
        "battery_power_scale": 1.00,
    },
    "Precios elevados": {
        "description": "Aumenta los precios electricos un 25 %.",
        "consumption_scale": 1.00,
        "pv_scale": 1.00,
        "price_scale": 1.25,
        "battery_capacity_scale": 1.00,
        "battery_power_scale": 1.00,
    },
    "Bateria ampliada": {
        "description": "Aumenta capacidad y potencia de bateria un 50 %.",
        "consumption_scale": 1.00,
        "pv_scale": 1.00,
        "price_scale": 1.00,
        "battery_capacity_scale": 1.50,
        "battery_power_scale": 1.50,
    },
    "Estres combinado": {
        "description": "Mayor demanda, menor PV y precios mas altos.",
        "consumption_scale": 1.20,
        "pv_scale": 0.75,
        "price_scale": 1.20,
        "battery_capacity_scale": 1.00,
        "battery_power_scale": 1.00,
    },
}

MIN_SOC_FRACTION = 0.20
TERMINAL_SOC_TOLERANCE = 1e-6
MAX_CYCLIC_DAYS = 20

# Hipotesis sencillas para mantener el simulador explicable en el TFM.
BATTERY_CHARGE_EFFICIENCY = 0.95
BATTERY_DISCHARGE_EFFICIENCY = 0.95
EXPORT_PRICE_FACTOR = 0.40
CSV_SEPARATOR = ";"
CSV_DECIMAL = ","
CSV_ENCODING = "utf-8-sig"

RULE_PRICE_THRESHOLD = 0.20
ADVANCED_PRICE_PERCENTILE = 70
PEAK_CONSUMPTION_THRESHOLD = 2.2
