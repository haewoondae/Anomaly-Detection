"""Check CLI env defaults without opening a DB connection or reading credentials."""
import argparse
import importlib
from pathlib import Path

import pytest

pytest.importorskip("pymysql")
pytest.importorskip("dotenv")


@pytest.mark.parametrize("name", ["phase2_extract", "phase2_candidate", "phase2_alarm_case", "phase2_waveform"])
def test_env_default_is_project_local_and_old_option_works(name, monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "repro"))
    module = importlib.import_module(name)
    monkeypatch.chdir(tmp_path)
    original_parse = argparse.ArgumentParser.parse_args

    class Checked(Exception):
        pass

    def check(parser):
        assert original_parse(parser, ["--targets", "unused.json"]).env_file == root / ".env"
        for option in ("--env-file", "--backend-env"):
            assert original_parse(parser, ["--targets", "unused.json", option, "custom.env"]).env_file == Path("custom.env")
        raise Checked

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", check)
    with pytest.raises(Checked):
        module.main()
