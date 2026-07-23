import os
import psycopg


def calculate_score(row):

    redfin_price = row.get("redfin_price") or 0
    last_sale_price = row.get("last_sale_price") or 0

    permits = row.get("building_permit_count_24m") or 0
    planning = row.get("planning_application_count_24m") or 0

    years_owned = row.get("years_owned") or 0


    # -------------------------
    # PROPERTY VALUE
    # -------------------------

    value_score = 0

    if redfin_price >= 1500000:
        value_score = 30
    elif redfin_price >= 1200000:
        value_score = 25
    elif redfin_price >= 900000:
        value_score = 20
    elif redfin_price >= 700000:
        value_score = 10


    # -------------------------
    # EQUITY
    # -------------------------

    equity_score = 0

    equity = redfin_price - last_sale_price

    if equity >= 1000000:
        equity_score = 15
    elif equity >= 750000:
        equity_score = 12
    elif equity >= 500000:
        equity_score = 8


    # -------------------------
    # PERMITS
    # -------------------------

    permit_score = min(permits * 5, 15)
    permit_score += min(planning * 5, 5)


    # -------------------------
    # OWNERSHIP LIFECYCLE
    # -------------------------

    lifecycle_score = 0

    if years_owned >= 25:
        lifecycle_score = 25
    elif years_owned >= 15:
        lifecycle_score = 18
    elif years_owned >= 10:
        lifecycle_score = 10


    # -------------------------
    # MARKET
    # -------------------------

    market_score = 5 if redfin_price else 0


    total = (
        value_score +
        equity_score +
        permit_score +
        lifecycle_score +
        market_score
    )


    if total >= 90:
        tier="HOT"
    elif total >= 75:
        tier="A"
    elif total >= 60:
        tier="B"
    elif total >= 40:
        tier="C"
    else:
        tier="D"


    return {
        "score": total,
        "tier": tier,
        "value_score": value_score,
        "equity_score": equity_score,
        "permit_score": permit_score,
        "lifecycle_score": lifecycle_score,
        "market_score": market_score
    }



def run():

    conn = psycopg.connect(os.environ["DATABASE_URL"])
    conn.row_factory = psycopg.rows.dict_row

    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM leads
    """)

    rows = cur.fetchall()

    print(f"Scoring {len(rows)} leads")


    for row in rows:

        score = calculate_score(row)

        cur.execute("""
        UPDATE leads
        SET
            prospect_score=%s,
            prospect_tier=%s,
            value_score=%s,
            equity_score=%s,
            permit_score=%s,
            lifecycle_score=%s,
            market_score=%s
        WHERE id=%s
        """,
        (
            score["score"],
            score["tier"],
            score["value_score"],
            score["equity_score"],
            score["permit_score"],
            score["lifecycle_score"],
            score["market_score"],
            row["id"]
        ))

    conn.commit()
    conn.close()

    print("Prospect scoring complete")


if __name__=="__main__":
    run()
