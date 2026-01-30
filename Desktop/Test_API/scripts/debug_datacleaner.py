import pandas as pd
import numpy as np
from logic import DataCleaner
import traceback

print('Creating sample csv...')
dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='MS')
data = {'mois': dates.strftime('%Y-%m-%d'), 'montant': np.random.uniform(1000, 50000, len(dates))}
df = pd.DataFrame(data)
csv_bytes = df.to_csv(index=False, sep=';').encode('utf-8')

with open('debug_datacleaner.log', 'w', encoding='utf-8') as f:
    try:
        f.write('Running DataCleaner...\n')
        cleaner = DataCleaner(csv_bytes)
        df_clean = cleaner.run()
        f.write(f'Cleaned months: {len(df_clean)}\n')
        f.write(df_clean.head().to_csv(sep=';'))
        f.write('\nLogs:\n')
        for l in cleaner.logs:
            f.write(' - ' + l + '\n')
    except Exception:
        import traceback
        f.write('EXCEPTION:\n')
        traceback.print_exc(file=f)

