import os
from datetime import datetime

import psycopg2
import psycopg2.extras


MAX_SCORE = 100


def safe_number(value):
    return value or 0



def calculate_score(row):

    signals = []

    redfin_price = safe_number(row.get("redfin_price"))
    last_sale_price = safe_number(row.get("last_sale_price"))

    permits = safe_number(
        row.get("building_permit_count_24m")
    )

    planning = safe_number(
        row.get("planning_application_count_24m")
    )

    years_owned = safe_number(
        row.get("years_owned")
    )


    # ----------------------------
    # OWNERSHIP SIGNAL
    # Highest predictor for Rossmoor
    # ----------------------------

    ownership_score = 0

    if years_owned >= 40:
        ownership_score = 30
        signals.append(
            f"Long ownership history ({years_owned} years)"
        )

    elif years_owned >= 25:
        ownership_score = 25
        signals.append(
            f"Established owner ({years_owned} years)"
        )

    elif years_owned >= 15:
        ownership_score = 15



    # ----------------------------
    # EQUITY SIGNAL
    # ----------------------------

    equity_score = 0

    equity = redfin_price - last_sale_price


    if equity >= 1500000:
        equity_score = 25
        signals.append(
            "Very high estimated equity"
        )

    elif equity >= 750000:
        equity_score = 18
        signals.append(
            "High estimated equity"
        )

    elif equity >= 300000:
        equity_score = 10



    # ----------------------------
    # PROPERTY VALUE
    # ----------------------------

    value_score = 0


    if redfin_price >= 1800000:
        value_score = 15
        signals.append(
            "Premium property value"
        )

    elif redfin_price >= 1200000:
        value_score = 12

    elif redfin_price >= 900000:
        value_score = 8



    # ----------------------------
    # HOME IMPROVEMENT SIGNAL
    # ----------------------------

    improvement_score = 0

    improvement_events = permits + planning


    if improvement_events >= 5:
        improvement_score = 15
        signals.append(
            "Recent property activity"
        )

    elif improvement_events >= 2:
        improvement_score = 8



    # ----------------------------
    # DATA QUALITY
    # ----------------------------

    fields_present = 0

    fields = [
        redfin_price,
        last_sale_price,
        years_owned,
        permits
    ]

    for field in fields:
        if field:
            fields_present += 1


    confidence = round(
        fields_present / len(fields),
        2
    )


    total = min(
        ownership_score +
        equity_score +
        value_score +
        improvement_score,
        MAX_SCORE
    )


    if total >= 85:
        tier="HOT"

    elif total >=70:
        tier="A"

    elif total >=55:
        tier="B"

    elif total >=40:
        tier="C"

    else:
        tier="D"


    return {

        "score": total,

        "tier": tier,

        "confidence": confidence,

        "signals": signals,

        "ownership_score":
            ownership_score,

        "equity_score":
            equity_score,

        "value_score":
            value_score,

        "improvement_score":
            improvement_score
    }



def run():

    conn = psycopg2.connect(
        os.environ["DATABASE_URL"]
    )

    cur = conn.cursor(
        cursor_factory=
        psycopg2.extras.RealDictCursor
    )


    cur.execute(
        """
        SELECT *
        FROM leads
        """
    )


    rows = cur.fetchall()


    print(
        f"Scoring {len(rows)} leads"
    )


    for row in rows:

        score = calculate_score(row)


        cur.execute(
            """
            UPDATE leads

            SET
                prospect_score=%s,
                prospect_tier=%s,

                score_confidence=%s,

                ownership_score=%s,
                equity_score=%s,
                value_score=%s,
                improvement_score=%s,

                score_signals=%s,

                scored_at=NOW()

            WHERE id=%s

            """,

            (
                score["score"],
                score["tier"],

                score["confidence"],

                score["ownership_score"],
                score["equity_score"],
                score["value_score"],
                score["improvement_score"],

                psycopg2.extras.Json(
                    score["signals"]
                ),

                row["id"]
            )
        )


    conn.commit()

    conn.close()


    print(
        "Lead scoring complete"
    )



if __name__ == "__main__":
    run()