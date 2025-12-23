import os
from pathlib import Path
import sys

# add parent directory to path so we can import autoPrediction
sys.path.insert(0, str(Path(__file__).parent.parent))

from autoPrediction import DataCleaner, SmartPredictor


def run_codes_interactive(input_folder='dataSets/ordonateurs', out_folder='dataSets/ordonateurs_forecasts'):
    os.makedirs(out_folder, exist_ok=True)

    # Ask user how they want to provide codes
    s = input('Nombre de codes à saisir (entier) ou laisser vide pour saisir une liste séparée par virgule: ').strip()
    codes = []
    if s == '':
        raw = input('Liste de codes (séparés par virgule): ').strip()
        codes = [c.strip() for c in raw.split(',') if c.strip()]
    else:
        try:
            n = int(s)
        except ValueError:
            print('Entrée invalide, annulation.')
            return
        for i in range(1, n + 1):
            c = input(f'Code #{i}: ').strip()
            if c:
                codes.append(c)

    if not codes:
        print('Aucun code fourni. Fin.')
        return

    # Ask months once for all codes
    mraw = input('Période de prévision en mois (ex: 12) pour tous les codes: ').strip()
    try:
        months = int(mraw)
    except Exception:
        print('Période invalide. Fin.')
        return

    run_codes_from_list(codes, months, input_folder=input_folder, out_folder=out_folder)


def run_codes_from_list(codes, months, input_folder='dataSets/ordonateurs', out_folder='dataSets/ordonateurs_forecasts'):
    os.makedirs(out_folder, exist_ok=True)
    summary = []
    for code in codes:
        p = os.path.join(input_folder, f"{code}.csv")
        if not os.path.exists(p):
            print(f"Fichier introuvable pour le code {code}: {p}")
            summary.append((code, 'missing', ''))
            continue

        try:
            print(f'-- NETTOYAGE : {code} --')
            cleaner = DataCleaner(p)
            df = cleaner.run()
            predictor = SmartPredictor(df)
            predictor.analyze_and_configure()
            out_path = os.path.join(out_folder, f"{code}_forecast.csv")
            predictor.predict(months=months, save_csv=True, out_path=out_path, dataset_name=code)
            summary.append((code, 'ok', out_path))
        except Exception as e:
            print(f'Erreur pour {code}: {e}')
            summary.append((code, f'error: {e}', ''))

    print('Finished. Résumé:')
    for row in summary:
        print(row)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run forecasts for specific ordonnateur codes')
    parser.add_argument('--codes', type=str, default=None, help='Comma-separated ordonnateur codes to run')
    parser.add_argument('--months', type=int, default=None, help='Months to forecast (required with --codes)')
    parser.add_argument('--input-folder', default='dataSets/ordonateurs')
    parser.add_argument('--out-folder', default='dataSets/ordonateurs_forecasts')
    args = parser.parse_args()

    if args.codes:
        codes = [c.strip() for c in args.codes.split(',') if c.strip()]
        if not args.months:
            print('When using --codes you must also provide --months')
        else:
            print(f'Running non-interactive for codes={codes} months={args.months}')
            run_codes_from_list(codes, args.months, input_folder=args.input_folder, out_folder=args.out_folder)
    else:
        run_codes_interactive()
