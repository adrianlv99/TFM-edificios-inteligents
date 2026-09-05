import numpy as np


def generate_consumption_profile(seed=1, scale=1.0):
    """Genera un perfil sintetico de consumo de 24 horas."""
    np.random.seed(seed)

    base_profile = np.array([
        1.2, 1.0, 0.9, 0.8, 0.8, 1.0,
        1.5, 2.2, 2.5, 2.0, 1.8, 1.7,
        1.9, 2.1, 2.0, 1.8, 2.2, 3.0,
        3.5, 3.2, 2.8, 2.3, 1.8, 1.4,
    ])

    noise = np.random.normal(0, 0.15, 24)
    return np.maximum((base_profile + noise) * scale, 0)


def generate_pv_profile(scale=1.0):
    """Genera un perfil sintetico de generacion fotovoltaica de 24 horas."""
    return np.array([
        0, 0, 0, 0, 0, 0,
        0.3, 0.8, 1.5, 2.4, 3.2, 3.8,
        4.0, 3.7, 3.0, 2.1, 1.2, 0.4,
        0, 0, 0, 0, 0, 0,
    ]) * scale


def generate_price_profile(scale=1.0):
    """Genera un perfil sintetico de precios de 24 horas en EUR/kWh."""
    return np.array([
        0.14, 0.13, 0.12, 0.12, 0.13, 0.15,
        0.18, 0.22, 0.24, 0.20, 0.17, 0.15,
        0.14, 0.15, 0.17, 0.20, 0.23, 0.28,
        0.30, 0.27, 0.24, 0.20, 0.17, 0.15,
    ]) * scale
