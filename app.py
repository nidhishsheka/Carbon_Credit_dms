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


@app.route("/add_establishment", methods=["GET","POST"])
def add_establishment():

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

    clean_rows = []

    for r in rows:
        clean_rows.append({
            "est_name": r["est_name"],
            "source_name": r["source_name"],
            "unit": r["unit"],
            "quantity": r["quantity"],
            "factor_value": r["factor_value"],
            "emission_kg": round(r["emission_kg"], 2)
        })

    return render_template("emissions.html", rows=clean_rows)


@app.route("/report")
def report():

    with sqlite3.connect("cc.db") as conn:
        conn.row_factory = sqlite3.Row

    rows = conn.execute("SELECT * FROM Carbon_Report_View").fetchall()


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