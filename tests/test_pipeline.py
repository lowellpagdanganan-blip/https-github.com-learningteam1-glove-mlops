from pathlib import Path

from dags.your_pipeline import run_pipeline


def test_run_pipeline_writes_output(tmp_path):
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"
    input_path.write_text("glove_id,score\n1,0.9\n2,0.8\n", encoding="utf-8")

    run_pipeline(str(input_path), str(output_path))

    assert output_path.exists()
    assert output_path.stat().st_size > 0
