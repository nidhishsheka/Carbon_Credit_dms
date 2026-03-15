import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("cc.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def dashboard():

    with sqlite3.connect("cc.db") as conn:
        conn.row_factory = sqlite3.Row

    total_est = conn.execute(
        "SELECT COUNT(*) FROM Establishment"
    ).fetchone()[0]

    total_act = conn.execute(
        "SELECT COUNT(*) FROM Activity_Data"
    ).fetchone()[0]

    total_em = conn.execute(
        "SELECT COUNT(*) FROM Emission_Record"
    ).fetchone()[0]

    return render_template(
        "dashboard.html",
        total_est=total_est,
        total_act=total_act,
        total_em=total_em
    )


@app.route("/add_entity", methods=["GET","POST"])
def add_entity():

    with sqlite3.connect("cc.db") as conn:
        conn.row_factory = sqlite3.Row
    sectors = conn.execute(
        "SELECT DISTINCT sector FROM Reduction_Policy"
        ).fetchall()

    if request.method == "POST":

        name = request.form["entity_name"]
        est_type = request.form["entity_type"]
        location = request.form["location"]

        baseline = request.form.get("baseline") or 9000
        baseline_year = request.form.get("baseline_year") or 2024

        

        cursor = conn.execute(
           "INSERT INTO Establishment (est_name, est_type, location) VALUES (?,?,?)",
           (name, est_type, location)
        )

        est_id = cursor.lastrowid

        conn.execute(
    "INSERT INTO Baseline_Emission (est_id, baseline_emission_kg, baseline_year) VALUES (?,?,?)",
    (est_id, baseline, baseline_year)
)

        conn.commit()

        return redirect("/")

    return render_template("add_entity.html", sectors=sectors)


@app.route("/add_activity", methods=["GET","POST"])
def add_activity():

    with sqlite3.connect("cc.db") as conn:
        conn.row_factory = sqlite3.Row

    establishments = conn.execute(
        "SELECT * FROM Establishment"
    ).fetchall()

    sources = conn.execute(
        "SELECT * FROM Emission_Source"
    ).fetchall()

    if request.method == "POST":

        est_id = request.form["est_id"]
        source_id = request.form["source_id"]
        quantity = float(request.form["quantity"])
        period = request.form["period"]

        # insert activity
        cursor = conn.execute(
            "INSERT INTO Activity_Data (est_id, source_id, quantity, period) VALUES (?,?,?,?)",
            (est_id, source_id, quantity, period)
        )

        activity_id = cursor.lastrowid

        # get emission factor
        factor = conn.execute(
            "SELECT factor_value FROM Emission_Factor WHERE source_id=?",
            (source_id,)
        ).fetchone()

        factor_value = factor["factor_value"]

        # calculate emission
        emission = quantity * factor_value

        # insert emission record
        conn.execute(
            "INSERT INTO Emission_Record (activity_id, emission_kg) VALUES (?,?)",
            (activity_id, emission)
        )

        conn.commit()

        return redirect("/emissions")

    return render_template(
        "add_activity.html",
        establishments=establishments,
        sources=sources
    )


@app.route("/emissions")
def emissions():

    with sqlite3.connect("cc.db") as conn:
        conn.row_factory = sqlite3.Row

    rows = conn.execute("""
    SELECT
      e.est_name,
      s.source_name,
      s.unit,
      ad.quantity,
      ef.factor_value,
      er.emission_kg

    FROM Emission_Record er

    JOIN Activity_Data ad
    ON er.activity_id = ad.activity_id

    JOIN Establishment e
    ON ad.est_id = e.est_id

    JOIN Emission_Source s
    ON ad.source_id = s.source_id

    JOIN Emission_Factor ef
    ON s.source_id = ef.source_id
    """).fetchall()

    return render_template("emissions.html", rows=rows)


@app.route("/report")
def report():

    with sqlite3.connect("cc.db") as conn:
        conn.row_factory = sqlite3.Row

    rows = conn.execute("""
    SELECT
 e.est_name,
 e.est_type AS sector,

 COALESCE(b.baseline_emission_kg,0) AS baseline_emission_kg,

 COALESCE(rp.reduction_percent,0) AS reduction_percent,

 ROUND(COALESCE(SUM(er.emission_kg),0),2) AS actual_emission,

 ROUND(COALESCE(b.baseline_emission_kg,0) *
 (1 - COALESCE(rp.reduction_percent,0)/100.0),2) AS allowed_limit,

 ROUND(
 (
 COALESCE(b.baseline_emission_kg,0) *
 (1 - COALESCE(rp.reduction_percent,0)/100.0)
 -
 COALESCE(SUM(er.emission_kg),0)
 )/1000.0,2) AS carbon_credit

FROM Establishment e

LEFT JOIN Baseline_Emission b
ON e.est_id = b.est_id

LEFT JOIN (SELECT DISTINCT sector, reduction_percent FROM Reduction_Policy) rp
ON e.est_type = rp.sector

LEFT JOIN Activity_Data ad
ON e.est_id = ad.est_id

LEFT JOIN Emission_Record er
ON ad.activity_id = er.activity_id

GROUP BY e.est_id;
    """).fetchall()


    data = []

    for r in rows:

        credit = r["carbon_credit"] if r["carbon_credit"] is not None else 0

        if credit > 0:
            status = "Surplus"
        elif credit < 0:
            status = "Deficit"
        else:
            status = "Neutral"

        data.append({
          "name": r["est_name"],
          "sector": r["sector"],
          "reduction": r["reduction_percent"] or 0,
          "baseline": r["baseline_emission_kg"],
          "allowed": r["allowed_limit"],
          "actual": r["actual_emission"],
          "credit": round(credit,2),
          "status": status
         })


    return render_template("report.html", rows=data)


if __name__ == "__main__":
    app.run(debug=True)