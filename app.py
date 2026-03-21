from flask import Flask, render_template, request
from main import run_analysis

app = Flask(__name__)

from flask import Flask, render_template, request, session
app.secret_key = "bullpen123"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    pteam = request.form.get("pteam")
    bteam = request.form.get("bteam")
    batter1 = request.form.get("batter1")
    batter2 = request.form.get("batter2")
    batter3 = request.form.get("batter3")

    result = run_analysis(pteam, bteam, batter1, batter2, batter3)

    if "error" in result:
        return render_template("index.html", error=result["error"])

    prev_results = session.get("prev_results", {})
    current_order = {r[1]: i+1 for i, r in enumerate(result["results"])}

    movements = {}
    if session.get("prev_team") == pteam:
        for name, rank in current_order.items():
            if name in prev_results:
                diff = prev_results[name] - rank
                movements[name] = diff

    session["prev_results"] = current_order
    session["prev_team"] = pteam

    return render_template("results.html", results=result["results"], movements=movements)


if __name__ == "__main__":
    app.run(debug=True)
