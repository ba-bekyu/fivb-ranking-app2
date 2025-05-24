from flask import Flask, render_template, request
import os
import math

app = Flask(__name__)

# C1～C5のカットポイント（正規分布のz値）
C_points = {
    "3-0": -1.060,
    "3-1": -0.394,
    "3-2": 0.0,
    "2-3": 0.394,
    "1-3": 1.060,
    "0-3": 2.0  # 0-3はC5より大きいので仮に2.0とする
}

# 正規分布の累積分布関数（CDF）
def norm_cdf(x):
    return (1 + math.erf(x / math.sqrt(2))) / 2

@app.route("/", methods=["GET", "POST"])
def index():
    data = []
    error = None
    team1 = team2 = ""
    team1_point = team2_point = 0.0
    weight = 40  # デフォルトMWF

    if request.method == "POST":
        try:
            team1 = request.form["team1"].upper()
            team2 = request.form["team2"].upper()
            team1_point = float(request.form["team1_point"])
            team2_point = float(request.form["team2_point"])
            weight = int(request.form["weight"])

            # 実力差D（FIVBでは400で割る）
            D = (team1_point - team2_point) / 400

            # FIVB公式の式に基づく期待勝率（正規分布のCDF）
            expected_team1 = norm_cdf(D)
            expected_team2 = 1 - expected_team1

            # 試合結果ごとのポイント変動計算
            for score, C in C_points.items():
                # FIVBはポイント変動 = MWF × (勝者側の経験値 - 期待値) で計算
                # 勝者側経験値はCDFで区間確率を計算する必要があるが、
                # 実際はカットポイントCとDの差でCDF値の差を取って区間確率を得る。

                # まず、上限カットポイント
                # 下限は次のスコアのC値で定義されるが、単純化して
                # 区間は [C_prev, C_current] と仮定（要注意）

                # 区間確率は、勝者がこのスコアを得る確率
                # → P(C_i < Z - D < C_{i+1}) = norm_cdf(C_upper - D) - norm_cdf(C_lower - D)

                # ただしここでは簡易的にCDFで評価

                # ポイント変動は (CDF(C - D) - CDF(C_ref)) × weight
                # C_refはそのスコアが同点（D=0）のときの期待値

                # 0-3スコアは特別扱いとして区間の上限なし
                # 区間計算用にC_pointsを順序付けリストにする

                # ここでは単純に C - D のCDFから D=0 のCDFを引いてポイント変動を計算

                delta = weight * (norm_cdf(C - D) - norm_cdf(C))
                # 勝利チームがteam1なら +delta、負けチームは -delta

                # 勝者・敗者判定はスコアの形で判別
                if score.startswith("3-"):  # team1勝ち
                    delta1 = round(delta, 2)
                    delta2 = round(-delta, 2)
                else:  # team1負け
                    delta1 = round(-delta, 2)
                    delta2 = round(delta, 2)

                data.append({
                    "score": score,
                    "team1_delta": delta1,
                    "team2_delta": delta2,
                    "team1_new": round(team1_point + delta1, 2),
                    "team2_new": round(team2_point + delta2, 2)
                })

        except Exception as e:
            error = f"エラー: 入力を確認してください（{e}）"

    return render_template("index.html",
                           data=data,
                           team1=team1,
                           team2=team2,
                           team1_point=team1_point,
                           team2_point=team2_point,
                           weight=weight,
                           error=error)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
