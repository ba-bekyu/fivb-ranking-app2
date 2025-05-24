from flask import Flask, render_template, request
import os
from scipy.stats import norm

app = Flask(__name__)

# カットポイント（C1〜C5）
C = {
    "3-0": -1.060,
    "3-1": -0.394,
    "3-2":  0.000,
    "2-3":  0.394,
    "1-3":  1.060,
    "0-3":  float("inf")  # 最後は1から引く
}

# セットスコアとSSV（Set Score Value）
ssv_map = {
    "3-0": +2.0,
    "3-1": +1.5,
    "3-2": +1.0,
    "2-3": -1.0,
    "1-3": -1.5,
    "0-3": -2.0
}

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    error = None
    team1 = team2 = ""
    rating1 = rating2 = 0.0
    mwf = 50  # デフォルトMWF

    if request.method == "POST":
        try:
            team1 = request.form["team1"]
            team2 = request.form["team2"]
            rating1 = float(request.form["rating1"])
            rating2 = float(request.form["rating2"])
            mwf = int(request.form["mwf"])

            delta = 8 * (rating1 - rating2) / 1000

            # 正規分布による結果確率
            prob = {}
            cutoffs = list(C.items())
            for i in range(len(cutoffs)):
                score, c_value = cutoffs[i]
                if score == "3-0":
                    p = norm.cdf(c_value + delta)
                elif score == "0-3":
                    p = 1 - norm.cdf(C["1-3"] + delta)
                else:
                    p = norm.cdf(c_value + delta) - norm.cdf(cutoffs[i - 1][1] + delta)
                prob[score] = p

            # EMR（Expected Match Result）
            emr = sum(prob[score] * ssv_map[score] for score in ssv_map)

            # 各試合結果ごとのポイント変動
            for score in ssv_map:
                actual_ssv = ssv_map[score]
                wr_value = actual_ssv - emr
                raw_delta = round(wr_value * mwf / 8, 3)

                # 最低保証ルール
                if actual_ssv > 0:  # 勝利
                    delta1 = max(raw_delta, 0.01)
                    delta2 = -delta1
                elif actual_ssv < 0:  # 敗北
                    delta1 = min(raw_delta, -0.01)
                    delta2 = -delta1
                else:
                    delta1 = delta2 = 0.0

                results.append({
                    "score": score,
                    "probability": round(prob[score] * 100, 2),
                    "team1_delta": round(delta1, 3),
                    "team2_delta": round(delta2, 3),
                    "team1_new": round(rating1 + delta1, 3),
                    "team2_new": round(rating2 + delta2, 3)
                })

        except Exception as e:
            error = f"エラー: {str(e)}"

    return render_template("index.html",
                           results=results,
                           team1=team1,
                           team2=team2,
                           rating1=rating1,
                           rating2=rating2,
                           mwf=mwf,
                           error=error)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
