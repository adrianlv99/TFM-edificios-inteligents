Simulador desarrollado para el TFM:
"Metodologia para la integracion de edificios inteligentes como recursos flexibles en sistemas electricos".

Descripcion general
-------------------
El codigo implementa un simulador multiagente sencillo, reproducible y orientado a validacion conceptual.
Cada edificio se representa mediante un agente BuildingAgent con perfiles horarios de consumo,
generacion fotovoltaica, bateria, precio electrico y reglas de decision.

La aplicacion puede ejecutarse con una interfaz grafica para analizar los resultados de forma visual
o en modo consola para conservar un flujo reproducible.

Escenarios simulados
--------------------
1. Sin control: operacion convencional. La PV cubre consumo local, el excedente se exporta y el deficit se cubre importando energia de la red. La bateria no se gestiona.
2. Reglas: control basado en reglas. Se prioriza autoconsumo, se carga la bateria con excedentes PV y se descarga cuando el precio es alto o existe demanda relevante.
3. Reglas + decision avanzada: apoyo avanzado a la decision mediante umbrales de precio, demanda y reserva de bateria. No usa una API ni un modelo real de IA; la integracion con Groq u otra API queda como trabajo futuro.

Casos de estudio
----------------
La GUI y el modo consola permiten elegir distintos casos antes de ejecutar la simulacion:
- Caso base: perfiles sinteticos originales.
- Alta demanda: aumenta el consumo un 20 %.
- Baja irradiacion: reduce la generacion fotovoltaica un 35 %.
- Precios elevados: aumenta los precios electricos un 25 %.
- Bateria ampliada: aumenta capacidad y potencia de bateria un 50 %.
- Estres combinado: mayor demanda, menor PV y precios mas altos.

Estos casos cambian las condiciones de entrada, mientras que los tres escenarios comparan las estrategias de gestion energetica bajo esas mismas condiciones.

Hipotesis del modelo
--------------------
- Horizonte de simulacion: 24 horas con resolucion horaria.
- Dos edificios con baterias independientes.
- Eficiencia de carga de bateria: 95 %.
- Eficiencia de descarga de bateria: 95 %.
- El coste energetico es neto: coste de energia importada menos compensacion por excedentes exportados.
- La compensacion por exportacion se aproxima como el 40 % del precio horario de compra.
- El pico agregado de red se calcula sumando primero la importacion de todos los edificios por escenario y hora, y tomando despues el maximo horario.
- Los CSV se exportan con separador de punto y coma, coma decimal y codificacion utf-8-sig para abrirlos correctamente en Excel con configuracion regional espanola.
- Todos los casos de estudio usan las mismas semillas de consumo por edificio. Esto garantiza comparabilidad: los casos Precios elevados y Bateria ampliada no modifican la importacion del escenario Sin control respecto al Caso base.
- El estado inicial y final de la bateria se exporta en las metricas para documentar el balance energetico.
- El SOC inicial se fija igual al SOC minimo tecnico del 20 % para evitar energia inicial gratuita.
- El simulador comprueba automaticamente que el SOC final coincide con el SOC inicial con tolerancia maxima de 1e-6 kWh.
- El archivo results/simulation_parameters.csv recoge parametros, umbrales, semillas, eficiencias y configuracion de baterias para reproducir el experimento.

Interfaz grafica
----------------
La GUI muestra:
- Resumen de indicadores principales.
- Metricas agregadas por escenario.
- Metricas por edificio.
- Graficas comparativas de importacion de red, coste neto, bateria, reducciones y autoconsumo PV.
- Detalle horario filtrable por escenario y edificio.
- Perfiles de entrada de PV, precio y consumo.
- Lista de CSV e imagenes generadas.

Archivos
--------
- main.py: punto de entrada de la aplicacion.
- config.py: escenarios, carpetas e hipotesis principales del modelo.
- simulation.py: ejecucion de escenarios y exportacion de resultados.
- building_agent.py: agente energetico y estrategias de operacion.
- data_generator.py: perfiles sinteticos de consumo, generacion fotovoltaica y precios.
- metrics.py: calculo de metricas por edificio, por escenario y series horarias agregadas.
- plots.py: generacion de graficas exportables.
- gui.py: interfaz grafica Tkinter con graficas matplotlib.
- results/simulation_results_all_scenarios.csv: resultados horarios completos.
- results/metrics_by_building.csv: metricas por edificio y escenario.
- results/metrics_by_scenario.csv: metricas agregadas por escenario.
- results/simulation_parameters.csv: parametros, semillas y umbrales usados en la simulacion.
- results/terminal_soc_equality.csv: prueba automatica de igualdad SOC inicial-final del caso ejecutado.
- results/metrics_by_scenario_all_cases.csv: metricas agregadas de los seis casos y tres estrategias.
- results/terminal_soc_equality_all_cases.csv: prueba SOC terminal para todos los casos, estrategias y edificios.
- figures/scenario_import_cost.png: comparacion de energia importada y coste neto.
- figures/scenario_battery_use.png: comparacion del uso de bateria.
- figures/scenario_reductions.png: reducciones frente al escenario Sin control del caso seleccionado.
- figures/hourly_grid_import_by_scenario.png: importacion agregada de red por hora.
- figures/hourly_battery_soc_by_scenario.png: estado de carga agregado por hora.

Ejecucion
---------
Desde la carpeta del proyecto:

python main.py

Si en Windows el comando anterior abre el alias de Microsoft Store o no localiza
el interprete, puede sustituirse python en los comandos siguientes por el
lanzador de Python o por la ruta completa al ejecutable instalado:

py -3 main.py

"C:\ruta\a\python.exe" main.py

Para ejecutar el modo consola:

python main.py --cli

Para ejecutar un caso concreto en consola:

python main.py --cli --case "Alta demanda"

Para ejecutar y exportar los seis casos de estudio:

python main.py --all-cases

Cada ejecucion actualiza los CSV de results/ y las imagenes de figures/. Los
archivos contienen los tres escenarios para el caso de estudio seleccionado en
esa ejecucion.

Requisitos
----------
- Python 3.9 o superior. Validado con Python 3.13.0.
- NumPy 2.2.4
- pandas 2.2.3
- Matplotlib 3.10.1
- tkinter Tcl/Tk 8.6, incluido normalmente con Python en Windows

Instalacion de dependencias Python:

python -m pip install -r requirements.txt

Nota metodologica
-----------------
Los perfiles utilizados son sinteticos y el objetivo es realizar una validacion conceptual y comparativa.
El simulador no pretende reproducir de forma exacta un sistema electrico real ni resolver una optimizacion avanzada.
