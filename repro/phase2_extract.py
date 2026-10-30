"""Bounded, SELECT-only Phase 2 extraction; run with the backend Python environment.

Credentials and target identifiers are supplied in ignored local files.
No waveform queries, database mutations, or algorithm changes are made here.
"""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import pymysql
from dotenv import dotenv_values


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--backend-env", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/phase2"))
    args = parser.parse_args()
    config = json.loads(args.targets.read_text(encoding="utf-8"))
    if config.get("status") != "approved":
        raise SystemExit("Target approval is required")
    start, end = config["from_ts_inclusive"], config["to_ts_exclusive"]
    start_dt, end_dt = map(datetime.fromisoformat, (start, end))
    if not 0 < (end_dt - start_dt).total_seconds() <= 31 * 86400:
        raise SystemExit("Expected a positive extraction period of at most 31 days")
    settings = dotenv_values(args.backend_env)
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    audit = []

    def select(cursor, name, sql, params):
        if not sql.lstrip().upper().startswith("SELECT ") or ";" in sql:
            raise ValueError("Only a single SELECT is allowed")
        audit.append({"name": name, "sql": sql, "params": params})
        write_json(out / "private/query_audit.json", audit)
        cursor.execute(sql, params)
        return cursor.fetchall()

    conn = None
    try:
        conn = pymysql.connect(
            host=settings["DB_HOST"], port=int(settings["DB_PORT"]),
            user=settings["DB_USER"], password=settings["DB_PASSWORD"],
            database=settings["DB_NAME"], connect_timeout=8,
            read_timeout=30, write_timeout=10, autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        )
        scope_where = ("t.SYS1_ID=%s AND t.COMPANY_ID=%s AND t.API_PORT=%s "
                       "AND t.POINT_ID=%s AND t.MEASUREMENT_ID=%s "
                       "AND t.AGGR_TIME_CD=%s AND t.VAL_TYPE=%s "
                       "AND t.TS >= %s AND t.TS < %s")

        def scope(channel):
            return tuple(channel[k] for k in ("SYS1_ID", "COMPANY_ID", "API_PORT",
                         "POINT_ID", "MEASUREMENT_ID", "AGGR_TIME_CD", "VAL_TYPE")) + (start, end)

        with conn.cursor() as cur:
            first = config["channels"][0]
            # Source metadata is restricted through a period/full-key trend EXISTS.
            tree = select(cur, "pilot_tree_scope", "SELECT b.SERVER_ID,b.API_PORT,"
                "b.LEVEL1_LOCAL_ID,b.LEVEL2_LOCAL_ID,b.LOCAL_ID,b.S_LOCAL_ID,b.ICON_GRP "
                "FROM TB_TREE_ALL b WHERE b.SERVER_ID=%s AND b.API_PORT=%s AND b.LOCAL_ID=%s "
                "AND EXISTS (SELECT 1 FROM TB_TREND_LOG_SKF t WHERE " + scope_where + ") LIMIT 3",
                (first["SYS1_ID"], first["API_PORT"], first["POINT_ID"]) + scope(first))
            write_json(out / "private/pilot_tree_scope.json", tree)
            if len(tree) != 1:
                raise ValueError("Pilot tree scope is absent or ambiguous")
            site = tree[0]
            # These tables have their own equipment/site keys, not measurement/aggregation keys.
            maintenance = select(cur, "site_maintenance_candidates", "SELECT SERVER_ID,API_PORT,"
                "LEVEL2_LOCAL_ID,EQUIPMENT_LOCAL_ID,ACTION_TS,ACTION_STATUS_CD,ACTION_CONTENT "
                "FROM TB_MAINTENANCE_ACTION WHERE SERVER_ID=%s AND API_PORT=%s "
                "AND LEVEL2_LOCAL_ID=%s AND ACTION_TS >= %s AND ACTION_TS < %s "
                "AND DELETE_YN <> 'Y' ORDER BY ACTION_TS LIMIT 201",
                (site["SERVER_ID"], site["API_PORT"], site["LEVEL2_LOCAL_ID"], start, end))
            alarms = select(cur, "site_alarm_candidates", "SELECT SYS1_ID,API_PORT,EVENT_ID,"
                "ENTERED_DATE_TIME,SEVERITY,ENTITY_LOCAL_ID,NODE_LOCAL_ID,POINT_LOCAL_ID,"
                "MEASUREMENT,TRIGGER_VALUE,LEVEL1_LOCAL_ID,LEVEL2_LOCAL_ID "
                "FROM TB_ALARM_EVENT WHERE SYS1_ID=%s AND API_PORT=%s "
                "AND LEVEL1_LOCAL_ID=%s AND LEVEL2_LOCAL_ID=%s "
                "AND ENTERED_DATE_TIME >= %s AND ENTERED_DATE_TIME < %s "
                "ORDER BY ENTERED_DATE_TIME LIMIT 201",
                (site["SERVER_ID"], site["API_PORT"], site["LEVEL1_LOCAL_ID"],
                 site["LEVEL2_LOCAL_ID"], start, end))
            write_json(out / "private/maintenance_candidates.json", maintenance)
            write_json(out / "private/alarm_candidates.json", alarms)
            if len(maintenance) > 200 or len(alarms) > 200:
                raise ValueError("Candidate discovery limit exceeded; narrow scope before continuing")
            write_json(out / "candidate_summary.json", {
                "site_alias": "site_A", "maintenance_records": len(maintenance),
                "alarm_records": len(alarms), "period": [start, end],
                "linked_second_equipment": "unconfirmed",
            })
            print(json.dumps({"maintenance_records": len(maintenance), "alarm_records": len(alarms)}), flush=True)
            inputs = []
            for ch in config["channels"]:
                if ch["SYS1_ID"] != "99":
                    raise ValueError("This pilot extractor only supports the approved SKF source")
                alias = ch["alias"]
                if alias not in ("VEL", "ACC", "ENV3"):
                    raise ValueError("Unexpected channel alias")
                meta = select(cur, alias + "_metadata", "SELECT s.MEASUREMENT_NM,s.MEASUREMENT_UNIT "
                    "FROM TB_EQUIP_SETPOINT s WHERE s.SYS1_ID=%s AND s.API_PORT=%s "
                    "AND s.LOCAL_ID=%s AND s.MEASUREMENT_ID=%s "
                    "AND EXISTS (SELECT 1 FROM TB_TREND_LOG_SKF t WHERE " + scope_where + ") LIMIT 3",
                    (ch["SYS1_ID"], ch["API_PORT"], ch["POINT_ID"], ch["MEASUREMENT_ID"]) + scope(ch))
                if len(meta) != 1 or meta[0]["MEASUREMENT_UNIT"] != ch["unit"]:
                    raise ValueError(alias + " metadata scope or unit mismatch")
                rows = select(cur, alias + "_trend", "SELECT t.SYS1_ID,t.COMPANY_ID,t.API_PORT,"
                    "t.POINT_ID,t.MEASUREMENT_ID,t.AGGR_TIME_CD,t.VAL_TYPE,t.TS,t.VAL "
                    "FROM TB_TREND_LOG_SKF t WHERE " + scope_where + " ORDER BY t.TS LIMIT 100001", scope(ch))
                if not rows or len(rows) > 100000:
                    raise ValueError(alias + " empty or over row cap")
                path = out / "inputs" / ("P-1_" + alias + ".csv")
                path.parent.mkdir(parents=True, exist_ok=True)
                fields = ["timestamps", "value", "source_ts", "unit", "SYS1_ID", "COMPANY_ID",
                          "API_PORT", "POINT_ID", "MEASUREMENT_ID", "AGGR_TIME_CD", "VAL_TYPE"]
                t0 = datetime.fromisoformat(rows[0]["TS"])
                with path.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow({"timestamps": (datetime.fromisoformat(row["TS"]) - t0).total_seconds(),
                            "value": row["VAL"], "source_ts": row["TS"], "unit": ch["unit"],
                            **{k: row[k] for k in fields[4:]}})
                inputs.append({"alias": alias, "path": path.as_posix(), "rows": len(rows),
                               "unit": ch["unit"], "metadata_history": "unconfirmed"})
                write_json(out / "private" / (alias + "_metadata.json"), meta)
                print(json.dumps({"channel": alias, "rows": len(rows)}), flush=True)
            write_json(out / "input_manifest.json", inputs)
            write_json(out / "extraction_status.json", {"status": "complete", "queries": len(audit)})
    except Exception as exc:
        write_json(out / "extraction_status.json", {"status": "stopped", "reason_type": type(exc).__name__,
                                                   "detail": str(exc)})
        print("STOP: extraction failed; inspect ignored extraction_status.json", flush=True)
        raise SystemExit(2)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
