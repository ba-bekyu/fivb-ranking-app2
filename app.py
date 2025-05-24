from flask import Flask, render_template, request

app = Flask(__name__)

# 試合結果と勝敗判定（勝ち=1.0、負け=0.0）
match_results = [
    ("3-0", 1.0),
    ("3-1", 1.0),
    ("3-2", 1.0),
    ("2-3", 0.0),
    ("1-3", 0.0),
    ("0-3", 0.0)
]

@app.route("/", methods=["GET", "POST"])
def index():
    data = []
    error = None
    team1 = team2 = ""
    team1_point = team2_point = 0.0
    weight = 40  # MWF（係数）

    if request.method == "POST":
        try:
            team1 = request.form["team1"].upper()
            team2 = request.form["team2"].upper()
            team1_point = float(request.form["team1_point"])
            team2_point = float(request.form["team2_point"])
            weight = int(request.form["weight"])

            # 期待値計算（勝つ確率の期待値）
            expected_team1 = 1 / (1 + 10 ** ((team2_point - team1_point) / 100))
            expected_team2 = 1 - expected_team1

            # 各試合結果ごとのポイント増減計算
            for score, outcome in match_results:
                if outcome == 1.0:  # team1勝ち
                    delta1 = round(weight * (1 - expected_team1), 2)
                    delta2 = round(weight * (0 - expected_team2), 2)
                else:  # team1負け
                    delta1 = round(weight * (0 - expected_team1), 2)
                    delta2 = round(weight * (1 - expected_team2), 2)

                data.append({
                    "score": score,
                    "team1_delta": delta1,
                    "team2_delta": delta2,
                    "team1_new": round(team1_point + delta1, 2),
                    "team2_new": round(team2_point + delta2, 2)
                })

        except Exception as e:
            error = f"入力エラーです。正しい値を入力してください。 ({e})"

    return render_template("index.html",
                           data=data,
                           team1=team1,
                           team2=team2,
                           team1_point=team1_point,
                           team2_point=team2_point,
                           weight=weight,
                           error=error)

if __name__ == "__main__":
    app.run(debug=True)
