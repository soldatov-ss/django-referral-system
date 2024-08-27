from io import StringIO

import pandas as pd


def parse_df_to_csv_string_without_index_col(df: pd.DataFrame) -> str:
    with StringIO() as buffer:
        df.to_csv(buffer, index=False)
        return buffer.getvalue()
