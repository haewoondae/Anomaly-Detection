"""Resolve and extract one alarm-linked second-equipment case, read-only."""
import argparse
import csv
from datetime import datetime
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
    cfg = json.loads(a.targets.read_text(encoding="utf-8"))
    if cfg["status"] != "approved":
        raise SystemExit("Approval required")
    out = Path("results/phase2")
    candidates = json.loads((out / "candidates/site_C/day/private/second_candidate_alarms.json").read_text(encoding="utf-8"))
    alarm = next(r for r in candidates if r["SEVERITY"] == 4)
    lo, hi = "2026-10-27 00:00:00", cfg["to_ts_exclusive"]
    keys = {"SYS1_ID": alarm["SYS1_ID"], "COMPANY_ID": cfg["second_candidate"]["COMPANY_ID"],
            "POINT_ID": alarm["ENTITY_LOCAL_ID"], "MEASUREMENT_ID": alarm["NODE_LOCAL_ID"], "AGGR_TIME_CD": "2M"}
    if keys["SYS1_ID"] != "04":
        raise SystemExit("Unsupported candidate source")
    env = dotenv_values(a.backend_env)
    conn = None
    audit = []
    try:
        conn = pymysql.connect(host=env["DB_HOST"], port=int(env["DB_PORT"]),
            user=env["DB_USER"], password=env["DB_PASSWORD"], database=env["DB_NAME"],
            connect_timeout=8, read_timeout=30, autocommit=True,
            cursorclass=pymysql.cursors.DictCursor)
        with conn.cursor() as cur:
            where = "t.SYS1_ID=%s AND t.COMPANY_ID=%s AND t.POINT_ID=%s AND t.MEASUREMENT_ID=%s AND t.AGGR_TIME_CD=%s AND t.TS >= %s AND t.TS < %s"
            params = tuple(keys.values()) + (lo, hi)
            sql = "SELECT s.MEASUREMENT_NM,s.MEASUREMENT_UNIT FROM TB_EQUIP_SETPOINT s WHERE s.SYS1_ID=%s AND s.LOCAL_ID=%s AND s.MEASUREMENT_ID=%s AND EXISTS (SELECT 1 FROM TB_TREND_LOG_SYS04 t WHERE " + where + ") LIMIT 3"
            mp = (keys["SYS1_ID"], keys["POINT_ID"], keys["MEASUREMENT_ID"]) + params
            audit.append({"name": "case_metadata", "sql": sql, "params": mp})
            cur.execute(sql, mp)
            meta = cur.fetchall()
            write_json(out / "private/alarm_case_metadata_candidates.json", meta)
            if len(meta) != 1 or meta[0]["MEASUREMENT_NM"] != alarm["MEASUREMENT"]:
                raise ValueError("Alarm/measurement mapping not confirmed")
            sql = "SELECT t.SYS1_ID,t.COMPANY_ID,t.POINT_ID,t.MEASUREMENT_ID,t.AGGR_TIME_CD,t.VAL_TYPE,t.TS,t.VAL FROM TB_TREND_LOG_SYS04 t WHERE " + where + " ORDER BY t.TS LIMIT 10001"
            audit.append({"name": "case_trend", "sql": sql, "params": params})
            cur.execute(sql, params)
            rows = cur.fetchall()
            if not rows or len(rows) > 10000:
                raise ValueError("Case data missing or cap exceeded")
            if len({r["VAL_TYPE"] for r in rows}) != 1:
                raise ValueError("Multiple value types in case; do not combine")
            duplicate = len(rows) - len({r["TS"] for r in rows})
            if duplicate:
                write_json(out / "STOP.json", {"reason": "Duplicate TS in second-equipment case", "duplicates": duplicate})
                raise ValueError("Duplicate TS; stop condition")
            write_json(out / "private/alarm_case_metadata.json", {"keys": keys, "metadata": meta, "alarm": alarm})
            path = out / "inputs/P-2_VEL.csv"
            t0 = datetime.fromisoformat(rows[0]["TS"])
            with path.open("w", encoding="utf-8", newline="") as stream:
                fields = ["timestamps", "value", "source_ts", "unit", *keys, "VAL_TYPE"]
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for row in rows:
                    writer.writerow({"timestamps": (datetime.fromisoformat(row["TS"]) - t0).total_seconds(),
                        "value": row["VAL"], "source_ts": row["TS"], "unit": meta[0]["MEASUREMENT_UNIT"],
                        **{k: row[k] for k in (*keys, "VAL_TYPE")}})
            linked = [r for r in candidates if r["ENTITY_LOCAL_ID"] == keys["POINT_ID"] and r["NODE_LOCAL_ID"] == keys["MEASUREMENT_ID"]]
            write_json(out / "alarm_case_labels.json", [{"source_ts": r["ENTERED_DATE_TIME"],
                "severity": r["SEVERITY"], "label_type": "weak_alarm", "timezone": "unconfirmed"} for r in linked])
            write_json(out / "alarm_case_status.json", {"status": "extracted", "site": "site_C", "equipment": "P-2",
                "rows": len(rows), "linked_alarms": len(linked), "mapping": "full source/site/point/channel and measurement name matched",
                "unit": meta[0]["MEASUREMENT_UNIT"], "timezone": "unconfirmed"})
            print(json.dumps({"case": "site_C / P-2", "rows": len(rows), "linked_alarms": len(linked)}), flush=True)
    except Exception as e:
        write_json(out / "alarm_case_stop.json", {"type": type(e).__name__, "detail": str(e)})
        print("STOP: case extraction failed; inspect ignored alarm_case_stop.json", flush=True)
        raise SystemExit(2)
    finally:
        write_json(out / "private/alarm_case_query_audit.json", audit)
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
