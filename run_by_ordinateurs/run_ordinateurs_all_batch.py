import os
from pathlib import Path
from datetime import datetime

from autoPrediction import DataCleaner, SmartPredictor


def run_all_batch(input_folder='dataSets/ordonateurs', out_folder='dataSets/ordonateurs_forecasts', months=12, limit=None):
    os.makedirs(out_folder, exist_ok=True)
    files = sorted(Path(input_folder).glob('*.csv'))
    if limit:
        files = files[:limit]

    summary = []
    for f in files:
        code = f.stem
        p = str(f)
        try:
            print(f'-- Processing {code} --')
            cleaner = DataCleaner(p)
            df = cleaner.run()
            predictor = SmartPredictor(df)
            predictor.analyze_and_configure()
            out_path = os.path.join(out_folder, f"{code}_forecast.csv")
            predictor.predict(months=months, save_csv=True, out_path=out_path, dataset_name=code)
            summary.append((code, 'ok', out_path))
        except Exception as e:
            print(f'Error for {code}: {e}')
            summary.append((code, f'error: {e}', ''))

    sfile = os.path.join(out_folder, f'summary_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv')
    with open(sfile, 'w', encoding='utf-8') as fh:
        fh.write('ordonateur,status,out_path\n')
        for row in summary:
            fh.write(f"{row[0]},{row[1]},{row[2]}\n")

    print(f'Done. Processed {len(summary)} files. Summary: {sfile}')
    return summary


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run non-interactive forecasts for all ordonnateurs')
    parser.add_argument('--input-folder', default='dataSets/ordonateurs')
    parser.add_argument('--out-folder', default='dataSets/ordonateurs_forecasts')
    parser.add_argument('--months', type=int, default=12)
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    run_all_batch(input_folder=args.input_folder, out_folder=args.out_folder, months=args.months, limit=args.limit)
