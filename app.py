from flask import Flask, render_template, request
from main import run_analysis

app = Flask(__name__)

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

    return render_template("results.html", results=result["results"])

if __name__ == "__main__":
    app.run(debug=True)
