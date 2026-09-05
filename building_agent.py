from config import (
    BATTERY_CHARGE_EFFICIENCY,
    BATTERY_DISCHARGE_EFFICIENCY,
    EXPORT_PRICE_FACTOR,
    SCENARIO_ADVANCED,
    SCENARIO_NO_CONTROL,
    SCENARIO_RULES,
)


class BuildingAgent:
    """
    Agente energetico que representa un edificio inteligente.

    El agente puede ejecutarse bajo tres estrategias de operacion:
    1. Operacion convencional sin gestion activa de bateria.
    2. Control basado en reglas.
    3. Control basado en reglas con apoyo avanzado a la decision.

    La tercera estrategia no usa IA real. Es una capa reproducible basada en
    umbrales de precio, demanda y reserva de bateria.
    """

    def __init__(
        self,
        name,
        battery_capacity,
        initial_soc,
        max_charge_power,
        max_discharge_power,
        min_soc=0.2,
        charge_efficiency=BATTERY_CHARGE_EFFICIENCY,
        discharge_efficiency=BATTERY_DISCHARGE_EFFICIENCY,
        export_price_factor=EXPORT_PRICE_FACTOR,
    ):
        self.name = name
        self.battery_capacity = battery_capacity
        self.soc = initial_soc
        self.initial_soc = initial_soc
        self.max_charge_power = max_charge_power
        self.max_discharge_power = max_discharge_power
        self.min_soc = min_soc
        self.charge_efficiency = charge_efficiency
        self.discharge_efficiency = discharge_efficiency
        self.export_price_factor = export_price_factor
        self.history = []

    def _register_result(
        self,
        scenario,
        hour,
        consumption,
        pv_generation,
        price,
        pv_used_directly,
        battery_charge_input,
        battery_charge,
        battery_discharge,
        battery_discharge_from_soc,
        battery_losses,
        grid_import,
        grid_export,
        decision,
    ):
        export_price = price * self.export_price_factor
        energy_purchase_cost = grid_import * price
        export_revenue = grid_export * export_price

        result = {
            "scenario": scenario,
            "hour": hour,
            "building": self.name,
            "battery_capacity": self.battery_capacity,
            "battery_initial_soc": self.initial_soc,
            "battery_min_soc": self.battery_capacity * self.min_soc,
            "max_charge_power": self.max_charge_power,
            "max_discharge_power": self.max_discharge_power,
            "charge_efficiency": self.charge_efficiency,
            "discharge_efficiency": self.discharge_efficiency,
            "export_price_factor": self.export_price_factor,
            "consumption": consumption,
            "pv_generation": pv_generation,
            "price": price,
            "export_price": export_price,
            "pv_used_directly": pv_used_directly,
            "battery_soc": self.soc,
            "battery_charge_input": battery_charge_input,
            "battery_charge": battery_charge,
            "battery_discharge": battery_discharge,
            "battery_discharge_from_soc": battery_discharge_from_soc,
            "battery_losses": battery_losses,
            "grid_import": grid_import,
            "grid_export": grid_export,
            "energy_purchase_cost": energy_purchase_cost,
            "export_revenue": export_revenue,
            "energy_cost": energy_purchase_cost - export_revenue,
            "decision": decision,
        }
        self.history.append(result)
        return result

    def _charge_battery_from_surplus(self, pv_surplus):
        if pv_surplus <= 0:
            return 0.0, 0.0, 0.0, pv_surplus

        available_capacity = max(0.0, self.battery_capacity - self.soc)
        max_input_by_capacity = available_capacity / self.charge_efficiency
        battery_charge_input = min(
            pv_surplus,
            max_input_by_capacity,
            self.max_charge_power,
        )
        battery_charge = battery_charge_input * self.charge_efficiency
        battery_losses = battery_charge_input - battery_charge

        self.soc += battery_charge
        grid_export = pv_surplus - battery_charge_input

        return battery_charge_input, battery_charge, battery_losses, grid_export

    def _discharge_battery_to_load(self, demand, reserve_fraction):
        if demand <= 0:
            return 0.0, 0.0, 0.0

        reserve_soc = self.battery_capacity * reserve_fraction
        available_soc = max(0.0, self.soc - reserve_soc)
        max_useful_output = available_soc * self.discharge_efficiency

        battery_discharge = min(
            demand,
            max_useful_output,
            self.max_discharge_power,
        )
        battery_discharge_from_soc = battery_discharge / self.discharge_efficiency
        battery_losses = battery_discharge_from_soc - battery_discharge

        self.soc -= battery_discharge_from_soc

        return battery_discharge, battery_discharge_from_soc, battery_losses

    def step_no_control(self, hour, consumption, pv_generation, price):
        """
        Escenario base: PV para consumo local, excedente exportado y deficit
        cubierto por la red. La bateria no se gestiona.
        """
        pv_used_directly = min(consumption, pv_generation)
        remaining_consumption = consumption - pv_used_directly
        pv_surplus = pv_generation - pv_used_directly

        return self._register_result(
            scenario=SCENARIO_NO_CONTROL,
            hour=hour,
            consumption=consumption,
            pv_generation=pv_generation,
            price=price,
            pv_used_directly=pv_used_directly,
            battery_charge_input=0.0,
            battery_charge=0.0,
            battery_discharge=0.0,
            battery_discharge_from_soc=0.0,
            battery_losses=0.0,
            grid_import=remaining_consumption,
            grid_export=pv_surplus,
            decision="Uso directo de PV e importacion/exportacion de red",
        )

    def step_rule_based(
        self,
        hour,
        consumption,
        pv_generation,
        price,
        high_price_threshold,
        peak_consumption_threshold,
    ):
        """
        Escenario de control basado en reglas interpretables.

        Reglas:
        - Priorizar autoconsumo fotovoltaico.
        - Cargar bateria con excedentes PV.
        - Descargar bateria si el precio es alto o queda una demanda relevante.
        - Respetar SOC minimo y eficiencia de carga/descarga.
        """
        pv_used_directly = min(consumption, pv_generation)
        remaining_consumption = consumption - pv_used_directly
        pv_surplus = pv_generation - pv_used_directly

        battery_charge_input = 0.0
        battery_charge = 0.0
        battery_discharge = 0.0
        battery_discharge_from_soc = 0.0
        battery_losses = 0.0
        grid_export = 0.0
        decision = []

        if pv_surplus > 0:
            (
                battery_charge_input,
                battery_charge,
                charge_losses,
                grid_export,
            ) = self._charge_battery_from_surplus(pv_surplus)
            battery_losses += charge_losses
            decision.append("Carga bateria con excedente PV")

        if remaining_consumption > 0:
            should_discharge = (
                price > high_price_threshold
                or remaining_consumption >= peak_consumption_threshold
            )

            if should_discharge:
                (
                    battery_discharge,
                    battery_discharge_from_soc,
                    discharge_losses,
                ) = self._discharge_battery_to_load(
                    demand=remaining_consumption,
                    reserve_fraction=self.min_soc,
                )
                battery_losses += discharge_losses

            grid_import = remaining_consumption - battery_discharge

            if battery_discharge > 0:
                decision.append("Descarga bateria por precio elevado o demanda alta")
            else:
                decision.append("Importa energia de red")
        else:
            grid_import = 0.0

        if not decision:
            decision.append("Autoconsumo PV suficiente")

        return self._register_result(
            scenario=SCENARIO_RULES,
            hour=hour,
            consumption=consumption,
            pv_generation=pv_generation,
            price=price,
            pv_used_directly=pv_used_directly,
            battery_charge_input=battery_charge_input,
            battery_charge=battery_charge,
            battery_discharge=battery_discharge,
            battery_discharge_from_soc=battery_discharge_from_soc,
            battery_losses=battery_losses,
            grid_import=grid_import,
            grid_export=grid_export,
            decision="; ".join(decision),
        )

    def step_advanced_decision(
        self,
        hour,
        consumption,
        pv_generation,
        price,
        high_price_threshold,
        peak_consumption_threshold,
    ):
        """
        Escenario de apoyo avanzado a la decision.

        No invoca modelos externos. Aplica una reserva dinamica de bateria por
        hora del dia y umbrales adaptativos de precio/demanda.
        """
        pv_used_directly = min(consumption, pv_generation)
        remaining_consumption = consumption - pv_used_directly
        pv_surplus = pv_generation - pv_used_directly

        battery_charge_input = 0.0
        battery_charge = 0.0
        battery_discharge = 0.0
        battery_discharge_from_soc = 0.0
        battery_losses = 0.0
        grid_export = 0.0
        decision = []

        if pv_surplus > 0:
            (
                battery_charge_input,
                battery_charge,
                charge_losses,
                grid_export,
            ) = self._charge_battery_from_surplus(pv_surplus)
            battery_losses += charge_losses
            decision.append("Carga bateria con excedente PV")

        if remaining_consumption > 0:
            reserve_fraction = 0.35 if hour < 16 else self.min_soc
            should_discharge = (
                price >= high_price_threshold
                or remaining_consumption >= peak_consumption_threshold
            )

            if should_discharge:
                (
                    battery_discharge,
                    battery_discharge_from_soc,
                    discharge_losses,
                ) = self._discharge_battery_to_load(
                    demand=remaining_consumption,
                    reserve_fraction=reserve_fraction,
                )
                battery_losses += discharge_losses

            grid_import = remaining_consumption - battery_discharge

            if battery_discharge > 0:
                decision.append("Descarga bateria por apoyo avanzado a la decision")
            else:
                decision.append("Reserva bateria e importa energia de red")
        else:
            grid_import = 0.0

        if not decision:
            decision.append("Autoconsumo PV suficiente")

        return self._register_result(
            scenario=SCENARIO_ADVANCED,
            hour=hour,
            consumption=consumption,
            pv_generation=pv_generation,
            price=price,
            pv_used_directly=pv_used_directly,
            battery_charge_input=battery_charge_input,
            battery_charge=battery_charge,
            battery_discharge=battery_discharge,
            battery_discharge_from_soc=battery_discharge_from_soc,
            battery_losses=battery_losses,
            grid_import=grid_import,
            grid_export=grid_export,
            decision="; ".join(decision),
        )
