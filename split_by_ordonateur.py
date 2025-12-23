import os
import argparse
import pandas as pd


def detect_separator(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        h = f.readline()
        return ';' if ';' in h else ','


def sanitize_filename(s: str) -> str:
    # Keep only safe chars
    keep = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    return ''.join(c if c in keep else '_' for c in str(s))


def split_by_ordonateur(input_csv: str, out_folder: str):
    sep = detect_separator(input_csv)
    df = pd.read_csv(input_csv, sep=sep, encoding='utf-8', low_memory=False)
    df.columns = df.columns.str.strip().str.lower()

    # detect columns
    col_date = next((c for c in df.columns if 'date' in c or 'jour' in c or 'reglement' in c), None)
    col_amount = next((c for c in df.columns if 'montant' in c or 'amount' in c or 'somme' in c or 'sum' in c), None)
    col_ord = next((c for c in df.columns if 'ordon' in c or 'ordonnat' in c or 'etabl' in c or 'code' in c), None)

    if not col_date or not col_amount or not col_ord:
        raise ValueError(f"Colonnes introuvables. Cherchées: date, montant, ordonnateur. Colonnes trouvées: {list(df.columns)}")

    # clean amount and date
    df['__amount'] = df[col_amount].astype(str).str.replace('\u00A0', '').str.replace(' ', '').str.replace(',', '.')
    df['__amount'] = pd.to_numeric(df['__amount'], errors='coerce')
    df['__date'] = pd.to_datetime(df[col_date], dayfirst=True, errors='coerce')

    df = df.dropna(subset=['__date', '__amount', col_ord])

    # aggregate by ordonnateur and date (daily), then write per ordonnateur aggregated by date
    df = df.set_index('__date')
    grouped = df.groupby([col_ord, pd.Grouper(freq='D')])['__amount'].sum().reset_index()

    os.makedirs(out_folder, exist_ok=True)
    written = 0
    for code, sub in grouped.groupby(col_ord):
        sub2 = sub[[ 'level_1' if 'level_1' in sub.columns else sub.columns[1], '__amount']]
        # fix columns: after reset_index names: [col_ord, 'index'/'__date']
        # safer: reconstruct
        sub_dates = sub.iloc[:, 1]
        df_out = pd.DataFrame({'date': sub_dates.dt.strftime('%Y-%m-%d'), 'montant': sub['__amount'].values})
        fname = sanitize_filename(code)
        out_path = os.path.join(out_folder, f"{fname}.csv")
        df_out.to_csv(out_path, index=False, sep=';')
        written += 1

    return written


def _cli():
    parser = argparse.ArgumentParser(description='Split dataset by ORDONNATEUR into separate CSVs')
    parser.add_argument('--input', default=os.path.join('dataSets', 'depensesEtat.csv'), help='Input CSV path')
    parser.add_argument('--out', default=os.path.join('dataSets', 'ordonateurs'), help='Output folder')
    args = parser.parse_args()

    n = split_by_ordonateur(args.input, args.out)
    print(f"Fichiers écrits: {n} dans {args.out}")


if __name__ == '__main__':
    _cli()
