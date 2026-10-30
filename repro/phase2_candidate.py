"""Investigate the preapproved second-channel candidate using bounded SELECTs."""
import argparse
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
    k = c["second_candidate"]
    tables = {"01": "TB_TREND_LOG_SYS01", "04": "TB_TREND_LOG_SYS04"}
    if k["SYS1_ID"] not in tables:
        raise SystemExit("Unknown candidate source")
    trend_table = tables[k["SYS1_ID"]]
    lo, hi = c["from_ts_inclusive"], c["to_ts_exclusive"]
    env = dotenv_values(a.backend_env)
    out = Path("results/phase2") / c.get("candidate_output_subdir", "")
    audit = []

    def select(cur, name, sql, params):
        if not sql.startswith("SELECT ") or ";" in sql:
            raise ValueError("Single SELECT required")
        audit.append({"name": name, "sql": sql, "params": params})
        write_json(out / "private/candidate_query_audit.json", audit)
        cur.execute(sql, params)
        rows = cur.fetchall()
        if len(rows) > 200:
            raise ValueError("Candidate discovery cap exceeded")
        return rows

    conn = None
    try:
        conn = pymysql.connect(host=env["DB_HOST"], port=int(env["DB_PORT"]),
            user=env["DB_USER"], password=env["DB_PASSWORD"], database=env["DB_NAME"],
            connect_timeout=8, read_timeout=30, autocommit=True,
            cursorclass=pymysql.cursors.DictCursor)
        with conn.cursor() as cur:
            tree = select(cur, "candidate_scope", "SELECT b.SERVER_ID,b.API_PORT,b.LOCAL_ID,"
                "b.LEVEL1_LOCAL_ID,b.LEVEL2_LOCAL_ID,b.S_LOCAL_ID "
                "FROM TB_TREE_ALL b WHERE b.SERVER_ID=%s AND b.LOCAL_ID=%s "
                "AND EXISTS (SELECT 1 FROM " + trend_table + " t WHERE t.SYS1_ID=%s "
                "AND t.COMPANY_ID=%s AND t.POINT_ID=%s AND t.MEASUREMENT_ID=%s "
                "AND t.AGGR_TIME_CD=%s AND t.TS >= %s AND t.TS < %s) LIMIT 3",
                (k["SYS1_ID"], k["POINT_ID"], k["SYS1_ID"], k["COMPANY_ID"], k["POINT_ID"],
                 k["MEASUREMENT_ID"], k["AGGR_TIME_CD"], lo, hi))
            write_json(out / "private/second_candidate_tree.json", tree)
            if len(tree) != 1:
                raise ValueError("Second candidate tree ambiguous or missing")
            t = tree[0]
            maintenance = select(cur, "candidate_site_maintenance", "SELECT SERVER_ID,API_PORT,"
                "LEVEL2_LOCAL_ID,EQUIPMENT_LOCAL_ID,ACTION_TS,ACTION_STATUS_CD,ACTION_CONTENT "
                "FROM TB_MAINTENANCE_ACTION WHERE SERVER_ID=%s AND API_PORT=%s "
                "AND LEVEL2_LOCAL_ID=%s AND ACTION_TS >= %s AND ACTION_TS < %s "
                "AND DELETE_YN <> 'Y' ORDER BY ACTION_TS LIMIT 201",
                (t["SERVER_ID"], t["API_PORT"], t["LEVEL2_LOCAL_ID"], lo, hi))
            point_clause = "AND (a.POINT_LOCAL_ID=%s OR a.ENTITY_LOCAL_ID=%s OR a.NODE_LOCAL_ID=%s) " if c.get("candidate_point_only") else ""
            point_params = (k["POINT_ID"],) * 3 if c.get("candidate_point_only") else ()
            alarms = select(cur, "candidate_site_alarms", "SELECT SYS1_ID,API_PORT,EVENT_ID,"
                "ENTERED_DATE_TIME,SEVERITY,ENTITY_LOCAL_ID,NODE_LOCAL_ID,POINT_LOCAL_ID,"
                "MEASUREMENT,TRIGGER_VALUE,LEVEL1_LOCAL_ID,LEVEL2_LOCAL_ID "
                "FROM TB_ALARM_EVENT a WHERE a.SYS1_ID=%s "
                "AND TRIM(COALESCE(a.API_PORT,''))=%s "
                "AND a.ENTERED_DATE_TIME >= %s AND a.ENTERED_DATE_TIME < %s "
                + point_clause +
                "AND EXISTS (SELECT 1 FROM TB_TREE_ALL b WHERE b.SERVER_ID=a.SYS1_ID "
                "AND TRIM(COALESCE(b.API_PORT,''))=TRIM(COALESCE(a.API_PORT,'')) "
                "AND b.LEVEL1_LOCAL_ID=%s AND b.LEVEL2_LOCAL_ID=%s "
                "AND (b.LOCAL_ID=CAST(a.ENTITY_LOCAL_ID AS CHAR) "
                "OR b.LOCAL_ID=CAST(a.NODE_LOCAL_ID AS CHAR) "
                "OR b.LOCAL_ID=CAST(a.POINT_LOCAL_ID AS CHAR))) "
                "ORDER BY a.ENTERED_DATE_TIME LIMIT 201",
                (t["SERVER_ID"], str(t["API_PORT"] or '').strip(), lo, hi) + point_params +
                (t["LEVEL1_LOCAL_ID"], t["LEVEL2_LOCAL_ID"]))
            write_json(out / "private/second_candidate_maintenance.json", maintenance)
            write_json(out / "private/second_candidate_alarms.json", alarms)
            direct = [r for r in alarms if str(k["POINT_ID"]) in
                      [str(r[f]) for f in ("ENTITY_LOCAL_ID", "NODE_LOCAL_ID", "POINT_LOCAL_ID")]]
            result = {"site_alias": c.get("site_alias", "site_B"), "candidate_alias": "P-2", "status": "investigated",
                "period": [lo, hi], "maintenance_records_in_site": len(maintenance),
                "alarm_records_in_site": len(alarms), "point_linked_alarm_records": len(direct),
                "measurement_link": "unconfirmed", "timezone": "unconfirmed"}
            write_json(out / "second_candidate_summary.json", result)
            print(json.dumps(result), flush=True)
    except Exception as e:
        write_json(out / "candidate_stop.json", {"type": type(e).__name__, "detail": str(e)})
        print("STOP: candidate investigation failed; inspect ignored candidate_stop.json", flush=True)
        raise SystemExit(2)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
