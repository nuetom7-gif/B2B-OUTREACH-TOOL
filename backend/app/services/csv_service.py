from io import BytesIO, StringIO

import pandas as pd


def read_csv_upload(contents: bytes) -> pd.DataFrame:
    return pd.read_csv(StringIO(contents.decode("utf-8-sig")))


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()


def normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def pick_field(row: dict, candidates: list[str]) -> str:
    normalized = {normalize_header(str(k)): v for k, v in row.items()}
    for candidate in candidates:
        key = normalize_header(candidate)
        if key in normalized and pd.notna(normalized[key]):
            return str(normalized[key]).strip()
    return ""


def split_list(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]
