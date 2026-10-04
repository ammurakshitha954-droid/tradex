"""
Market data validation and look-ahead bias prevention guards.
"""
from typing import Tuple, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np


class DataValidationError(Exception):
    pass


class MarketDataValidator:
    REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]

    @classmethod
    def validate_ohlcv(cls, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if df.empty:
            errors.append("DataFrame is empty.")
            return False, errors

        # Case-insensitive column normalization
        cols_lower = {c: c.lower() for c in df.columns}
        df_norm = df.rename(columns=cols_lower)

        for col in cls.REQUIRED_COLUMNS:
            if col not in df_norm.columns:
                errors.append(f"Missing required OHLCV column: '{col}'.")

        if errors:
            return False, errors

        # Check for NaN / infinite values
        for col in cls.REQUIRED_COLUMNS:
            if df_norm[col].isna().any():
                errors.append(f"Column '{col}' contains NaN values.")
            if np.isinf(df_norm[col]).any():
                errors.append(f"Column '{col}' contains infinite values.")

        # Price sanity check
        if (df_norm["low"] > df_norm["high"]).any():
            errors.append("Invariant violated: Low price is greater than High price.")
        if (df_norm["open"] < 0).any() or (df_norm["close"] < 0).any():
            errors.append("Invariant violated: Negative price detected.")
        if (df_norm["volume"] < 0).any():
            errors.append("Invariant violated: Negative volume detected.")

        # Check datetime index ordering
        if not isinstance(df.index, pd.DatetimeIndex):
            errors.append("Index must be a pandas DatetimeIndex.")
        else:
            if not df.index.is_monotonic_increasing:
                errors.append("Index timestamps must be monotonically increasing.")

        return len(errors) == 0, errors

    @classmethod
    def prevent_lookahead_slice(
        cls, 
        df: pd.DataFrame, 
        as_of_time: datetime
    ) -> pd.DataFrame:
        """
        Enforces strict zero look-ahead bias by pruning any records strictly after as_of_time.
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise DataValidationError("DataFrame must have DatetimeIndex for look-ahead protection.")
        
        sliced = df[df.index <= as_of_time].copy()
        if sliced.empty:
            raise DataValidationError(f"No historical data available prior to as_of_time: {as_of_time}")
        return sliced
