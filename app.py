import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("cc.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def dashboard():

    conn = get_db()

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

    if request.method == "POST":

        name = request.form["entity_name"]
        est_type = request.form["entity_type"]
        location = request.form["location"]

        conn = get_db()

        conn.execute(
            "INSERT INTO Establishment (est_name, est_type, location) VALUES (?,?,?)",
            (name, est_type, location)
        )

        conn.commit()

        return redirect("/")

    return render_template("add_entity.html")


@app.route("/add_activity", methods=["GET","POST"])
def add_activity():

    conn = get_db()

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

    conn = get_db()

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

    conn = get_db()

    rows = conn.execute("""
    SELECT
    e.est_name,
    b.baseline_emission_kg,
    a.allowed_emission_kg,
    COALESCE(SUM(er.emission_kg),0) as actual_emission,

    (a.allowed_emission_kg - COALESCE(SUM(er.emission_kg),0))/1000.0 as carbon_credit

    

    FROM Establishment e

    LEFT JOIN Baseline_Emission b
    ON e.est_id = b.est_id

    LEFT JOIN Allowed_Limit a
    ON b.baseline_id = a.baseline_id

    LEFT JOIN Activity_Data ad
    ON e.est_id = ad.est_id

    LEFT JOIN Emission_Record er
    ON ad.activity_id = er.activity_id

    GROUP BY e.est_id
    """).fetchall()


    data = []

    for r in rows:

        credit = r["carbon_credit"]

        if credit > 0:
            status = "Surplus"
        elif credit < 0:
            status = "Deficit"
        else:
            status = "Neutral"

        data.append({
            "name": r["est_name"],
            "baseline": r["baseline_emission_kg"],
            "allowed": r["allowed_emission_kg"],
            "actual": r["actual_emission"],
            "credit": round(credit,2),
            "status": status
        })


    return render_template("report.html", rows=data)


if __name__ == "__main__":
    app.run(debug=True)