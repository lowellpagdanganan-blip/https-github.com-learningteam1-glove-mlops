from pathlib import Path
import pandas as pd


def run_pipeline(input_csv: str, output_csv: str) -> None:
    input_path = Path(input_csv)
    output_path = Path(output_csv)
    df = pd.read_csv(input_path)
    df = df.dropna(subset=["glove_id"]).copy()
    df["processed"] = True
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    run_pipeline("data/raw/glove_test_extract.csv", "data/processed/glove_test_processed.csv")
