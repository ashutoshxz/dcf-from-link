
from pathlib import Path
import pandas as pd

def write_excel(output_dir: Path, forecast: pd.DataFrame, assumptions: dict, summary: dict):
    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx = output_dir / "model.xlsx"

    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        pd.DataFrame([summary]).to_excel(writer, sheet_name="Summary", index=False)
        pd.DataFrame([assumptions]).to_excel(writer, sheet_name="Assumptions", index=False)
        forecast.to_excel(writer, sheet_name="DCF", index=False)
