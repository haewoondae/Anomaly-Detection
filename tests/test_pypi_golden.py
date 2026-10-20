import json, os, sys
import pandas as pd, pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from osESD import osESD

DATA = os.environ.get("OSESD_DATA")
G = json.load(open(os.path.join(os.path.dirname(__file__), "golden_pypi_A.json")))

@pytest.mark.skipif(not DATA, reason="set OSESD_DATA to the osESD_R/data folder")
@pytest.mark.parametrize("key", sorted(G))
def test_author_mode_matches_pypi_golden(key):
    f = key.split("|")[0]
    df = pd.read_csv(os.path.join(DATA, f))
    idx = osESD(df, value_name="value", anomaly_name="anomaly", size=100, dwin=5, rwin=5,
                maxr=10, alpha=0.01, condition=True, use_author_lambda=True, rep_at="author")
    assert [int(i) for i in idx] == G[key]
