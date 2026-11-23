"""Standalone Colombo tea auction forecast dashboard."""

from datetime import date, datetime, timedelta
from functools import lru_cache
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, render_template, request
import joblib
import pandas as pd


app = Flask(__name__)
ASSETS = Path(__file__).resolve().parent / "dashboard_assets"
AUCTION_TZ = ZoneInfo("Asia/Colombo")
ACCURACY_TOLERANCE_LKR = 50
METHOD_TYPES = {
    "Last published price": "Benchmark",
    "Random Forest": "Bagging",
    "Extra Trees": "Randomized trees",
    "XGBoost": "Boosting",
    "CatBoost": "Boosting",
    "LightGBM": "Boosting",
    "Random Forest + XGBoost stack": "Stacking",
}
TEA_FIELDS = {
    "catalogue": "Catalogue",
    "category": "Category",
    "elevation": "Elevation",
    "segment": "Market segment",
    "grade": "Tea grade",
    "tier": "Quality tier",
    "region": "Growing region",
}
TEA_ACRONYMS = {"bop", "bop1", "bopf", "fbop", "fbopf", "op", "opa", "ctc", "pf1", "pd"}


def display_name(value):
    if value == "unknown":
        return "Not reported"
    return " ".join(
        word.upper() if word in TEA_ACRONYMS else word.title()
        for word in value.split("_")
    )


def group_label(group):
    keys = ("catalogue", "category", "grade", "tier", "segment", "elevation", "region")
    details = [display_name(group[key]) for key in keys if group[key] != "unknown"]
    return " · ".join(dict.fromkeys(details))


@lru_cache(maxsize=1)
def load_data():
    metadata = json.loads((ASSETS / "metadata.json").read_text(encoding="utf-8"))
    groups = pd.read_csv(ASSETS / "tea_groups.csv", dtype=str, keep_default_na=False).to_dict("records")
    scores = pd.read_csv(ASSETS / "test_scores.csv").to_dict("records")
    predictions = pd.read_csv(ASSETS / "test_predictions.csv", dtype={"target_date": str})
    return metadata, groups, scores, predictions


@lru_cache(maxsize=1)
def load_models():
    return joblib.load(ASSETS / "models.joblib")


def forecast_prices(bundle, group, auction_date, last_price):
    features = {
        **{key: group[key] for key in bundle["tea_features"]},
        "last_price_mid_lkr": last_price,
        "next_auction_month": auction_date.month,
    }
    inputs = pd.DataFrame([features], columns=bundle["features"])
    changes = pd.DataFrame({name: model.predict(inputs) for name, model in bundle["models"].items()})
    changes[bundle["stack_name"]] = bundle["combiner"].predict(changes[bundle["stack_inputs"]])
    prices = changes.iloc[0].add(last_price).to_dict()
    prices[bundle["baseline_name"]] = last_price
    return prices


def quotation_choices(groups, submitted):
    """Resolve the selected prefix, showing the next supported choice."""
    matches = groups
    fields = {}
    corrected = False
    blocked = False
    for key in TEA_FIELDS:
        options = sorted({group[key] for group in matches}, key=lambda value: (value == "unknown", value)) if not blocked else []
        value = submitted[key]
        selected = value if value in options else options[0] if len(options) == 1 else ""
        corrected |= bool(value and value != selected)
        fields[key] = {"options": options, "value": selected, "hidden": not options or options == ["unknown"]}
        if selected:
            matches = [group for group in matches if group[key] == selected]
        else:
            blocked = True
    return fields, matches[0] if not blocked and len(matches) == 1 else None, corrected


@app.route("/", methods=["GET", "POST"])
def forecast():
    metadata, groups, scores, _ = load_data()
    today = datetime.now(AUCTION_TZ).date()
    descriptors = {key: request.form.get(key, "") for key in TEA_FIELDS}
    labels = {
        key: {value: display_name(value) for value in sorted(
            {group[key] for group in groups}, key=lambda value: (value == "unknown", value)
        )}
        for key in TEA_FIELDS
    }
    choices, selected, corrected = quotation_choices(groups, descriptors)
    values = {
        "auction_date": request.form.get("auction_date", (today + timedelta(days=7)).isoformat()),
        "last_price": request.form.get("last_price", ""),
    }
    error = None
    notice = None
    estimates = None
    if request.method == "POST" and request.form.get("action") != "update":
        if selected is None or corrected:
            notice = "The available choices have been refreshed. Review them before estimating prices."
        else:
            try:
                auction_date = date.fromisoformat(values["auction_date"])
                last_price = float(values["last_price"])
                if auction_date < today or not math.isfinite(last_price) or last_price <= 0:
                    raise ValueError
            except ValueError:
                error = "Choose an upcoming auction date and enter a positive published price."
            else:
                estimates = forecast_prices(load_models(), selected, auction_date, last_price)
    return render_template(
        "forecast.html", active="forecast", metadata=metadata, groups=groups,
        fields=TEA_FIELDS, choices=choices, labels=labels, notice=notice,
        forecast_js_version=(Path(app.static_folder) / "forecast.js").stat().st_mtime_ns,
        scores=scores, values=values, today=today.isoformat(), error=error,
        estimates=estimates, selected=selected, method_types=METHOD_TYPES,
        display_name=display_name, group_label=group_label,
    )


@app.get("/overview")
def overview():
    metadata, groups, scores, _ = load_data()
    return render_template(
        "overview.html", active="overview", metadata=metadata, group_count=len(groups),
        benchmark=scores[0],
    )


@app.get("/results")
def results():
    metadata, _, scores, predictions = load_data()
    target = metadata["target"]
    scores = [
        {
            **score,
            "accuracy_pct": 100 * (predictions[target] - predictions[score["method"]])
            .abs().le(ACCURACY_TOLERANCE_LKR).mean(),
        }
        for score in scores
    ]
    methods = [score["method"] for score in scores]
    dates = sorted(predictions["target_date"].unique(), reverse=True)
    method = request.args.get("method", metadata["best_model"])
    auction = request.args.get("auction", "")
    if method not in methods:
        method = metadata["best_model"]
    if auction not in dates:
        auction = ""
    selected = predictions if not auction else predictions.loc[predictions["target_date"].eq(auction)]
    points = [
        {"actual": actual, "forecast": predicted, "catalogue": display_name(catalogue),
         "category": display_name(category), "date": day}
        for actual, predicted, catalogue, category, day in selected[
            [metadata["target"], method, "catalogue", "category", "target_date"]
        ].itertuples(index=False, name=None)
    ]
    selected_errors = (selected[target] - selected[method]).abs()
    benchmark = next(score for score in scores if score["method"] == metadata["benchmark"])
    best = next(score for score in scores if score["method"] == metadata["best_model"])
    best_accuracy = max(
        (score for score in scores if score["method"] != metadata["benchmark"]),
        key=lambda score: score["accuracy_pct"],
    )
    return render_template(
        "results.html", active="results", metadata=metadata, scores=scores, methods=methods,
        dates=dates, method=method, auction=auction, points=points, benchmark=benchmark,
        best=best, best_accuracy=best_accuracy, method_types=METHOD_TYPES,
        accuracy_tolerance=ACCURACY_TOLERANCE_LKR, selected_mae=selected_errors.mean(),
        selected_accuracy=100 * selected_errors.le(ACCURACY_TOLERANCE_LKR).mean(),
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)

