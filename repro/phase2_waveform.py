"""Read only metadata of snapshots within six hours of one detected change."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path

import pymysql
from dotenv import dotenv_values
from phase2_extract import write_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--targets", type=Path, required=True)
    p.add_argument("--backend-env", type=Path, required=True)
    a = p.parse_args()
    c = json.loads(a.targets.read_text(encoding="utf-8"))
    if c["status"] != "approved":
        raise SystemExit("Approval required")
    key = next(k for k in c["channels"] if k["alias"] == "VEL")
    event = datetime.fromisoformat("2026-10-12 11:33:00")
    lo, hi = (event - timedelta(hours=6)).isoformat(sep=" "), (event + timedelta(hours=6)).isoformat(sep=" ")
    env = dotenv_values(a.backend_env)
    conn = None
    out = Path("results/phase2")
    try:
        conn = pymysql.connect(host=env["DB_HOST"], port=int(env["DB_PORT"]),
            user=env["DB_USER"], password=env["DB_PASSWORD"], database=env["DB_NAME"],
            connect_timeout=8, read_timeout=30, autocommit=True, cursorclass=pymysql.cursors.DictCursor)
        params = tuple(key[k] for k in ("SYS1_ID", "COMPANY_ID", "API_PORT", "POINT_ID", "MEASUREMENT_ID")) + (lo, hi)
        sql = "SELECT w.UTC_TIME_STAMP,w.SAMPLING_PERIOD,w.NO_OF_DATA,w.UNIT_NAME,w.RPM,w.FMAX FROM TB_WAVEFORM_LOG_SKF w WHERE w.SYS1_ID=%s AND w.COMPANY_ID=%s AND w.API_PORT=%s AND w.POINT_ID=%s AND w.MEASUREMENT_ID=%s AND w.UTC_TIME_STAMP >= %s AND w.UTC_TIME_STAMP < %s AND EXISTS (SELECT 1 FROM TB_TREND_LOG_SKF t WHERE t.SYS1_ID=w.SYS1_ID AND t.COMPANY_ID=w.COMPANY_ID AND t.API_PORT=w.API_PORT AND t.POINT_ID=w.POINT_ID AND t.MEASUREMENT_ID=w.MEASUREMENT_ID AND t.AGGR_TIME_CD=%s AND t.TS >= %s AND t.TS < %s) ORDER BY w.UTC_TIME_STAMP LIMIT 3"
        params += (key["AGGR_TIME_CD"], lo, hi)
        write_json(out / "private/waveform_query_audit.json", {"sql": sql, "params": params})
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        if len(rows) > 2:
            raise ValueError("Unexpected snapshot count; narrow query")
        write_json(out / "waveform_link.json", {"site": "site_A", "equipment": "P-1", "channel": "VEL",
            "event_ts": str(event), "snapshots": rows, "alignment": "unconfirmed timezones; nominal raw timestamps only",
            "frequency_features": "not calculated; sampling/RPM unconfirmed", "label": "unconfirmed change, not TP/FP/FN"})
        print(json.dumps({"snapshot_metadata_rows": len(rows), "raw_waveform_arrays_read": 0}), flush=True)
    except Exception as e:
        write_json(out / "waveform_stop.json", {"type": type(e).__name__, "detail": str(e)})
        print("STOP: waveform metadata query failed; inspect ignored waveform_stop.json", flush=True)
        raise SystemExit(2)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
