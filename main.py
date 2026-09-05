import argparse

from config import DEFAULT_STUDY_CASE, STUDY_CASES
from simulation import run_all_study_cases, run_simulation


def main():
    parser = argparse.ArgumentParser(
        description="Simulador multiagente de edificios inteligentes."
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Ejecuta la simulacion en consola y genera CSV/imagenes.",
    )
    parser.add_argument(
        "--case",
        default=DEFAULT_STUDY_CASE,
        choices=list(STUDY_CASES.keys()),
        help="Caso de estudio a simular.",
    )
    parser.add_argument(
        "--all-cases",
        action="store_true",
        help="Ejecuta y exporta los seis casos de estudio.",
    )
    args = parser.parse_args()

    if args.all_cases:
        run_all_study_cases(export=True, print_summary=True)
        return

    if args.cli:
        run_simulation(export=True, print_summary=True, study_case_name=args.case)
        return

    from gui import launch_gui

    launch_gui()


if __name__ == "__main__":
    main()
