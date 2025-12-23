import os
from pathlib import Path
import sys

# add parent directory to path so we can import autoPrediction
sys.path.insert(0, str(Path(__file__).parent.parent))

from autoPrediction import DataCleaner, SmartPredictor


def run_all_prompt_per_dataset(input_folder='dataSets/ordonateurs', out_folder='dataSets/ordonateurs_forecasts', limit=None):
    os.makedirs(out_folder, exist_ok=True)
    print(f'Reading files from {input_folder}...')
    files = sorted(Path(input_folder).glob('*.csv'))
    print(f'Found {len(files)} files.')
    if limit:
        files = files[:limit]
        print(f'Limited to {len(files)} files.')

    summary = []
    for f in files:
        code = f.stem
        p = str(f)
        try:
            cleaner = DataCleaner(p)
            df = cleaner.run()
            print(f"Ordonnateur: {code} — mois disponibles: {len(df)}")
            # ask repeatedly until valid integer or explicit skip/quit
            quit_all = False
            skip = False
            months = None
            while True:
                raw = input(f"Nombre de mois à prédire pour {code} (entier), 's' pour sauter, 'q' pour quitter: ").strip()
                if raw.lower() == 'q':
                    print('Interrompu par l\'utilisateur.')
                    quit_all = True
                    break
                if raw.lower() == 's':
                    print(f'Skipping {code}')
                    skip = True
                    break
                if raw == '':
                    print('Entrée vide — entrez un entier, ou s pour sauter, q pour quitter.')
                    continue
                try:
                    months = int(raw)
                    break
                except Exception:
                    print('Entrée invalide — entrez un entier, ou s pour sauter, q pour quitter.')

            if quit_all:
                break
            if skip:
                summary.append((code, 'skipped', ''))
                continue

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

    parser = argparse.ArgumentParser(description='Run forecasts with per-dataset month prompts')
    parser.add_argument('--input-folder', default='dataSets/ordonateurs', help='Folder with ordonnateur CSVs')
    parser.add_argument('--out-folder', default='dataSets/ordonateurs_forecasts', help='Folder for forecasts')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of files (for testing)')
    parser.add_argument('--default-months', type=int, default=None, help='Default months if stdin is unavailable (for automation)')
    args = parser.parse_args()

    print(f'Starting... input_folder={args.input_folder}, limit={args.limit}')
    
    # Monkey-patch input if default_months is provided
    if args.default_months is not None:
        import builtins
        orig_input = builtins.input
        call_count = [0]
        def mock_input(prompt=''):
            call_count[0] += 1
            if call_count[0] == 1:  # first call per dataset
                print(prompt + str(args.default_months))
                return str(args.default_months)
            else:
                return orig_input(prompt)
        builtins.input = mock_input
    
    run_all_prompt_per_dataset(input_folder=args.input_folder, out_folder=args.out_folder, limit=args.limit)
