# Colombo Tea Auction Forecast

Estimate the next auction's reported price midpoint for a recurring tea quotation group in Sri Lanka. Choose the seven tea descriptors using linked selectors, select the upcoming date, and enter the group's latest published midpoint in LKR. The sidebar links to the overview, forecast form, and model comparison. The app compares five standalone models, a Random Forest + XGBoost stack, and the last-price benchmark.

## Run locally

Use **Python 3.12** and run these commands from the project folder.

```sh
python -m pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The Flask app loads fitted preprocessing and models from `dashboard_assets/`. Run `train_and_compare.ipynb` with the source CSV to reproduce the experiment and regenerate the assets.

## Repository contents

Commit `app.py`, `templates/`, `static/`, `requirements.txt`, and the complete `dashboard_assets/` folder. Include the notebook and source CSV for reproducibility. The Python entry point is the Flask WSGI application `app:app`.

## Test results and scope

The nine inputs are seven tea descriptors, the month of the upcoming auction, and the last published midpoint. Each model estimates how much the price will change. The backtest uses 1,764 matched quotations across 17 reserved auctions. The last-price benchmark won overall with **LKR 36.05 MAE**. The stack was the best ML model at **LKR 36.74 MAE**. The **Test results** tab has the full comparison and an interactive predicted-versus-recorded chart.

The estimate describes a broker quotation group. It uses the latest midpoint supplied by the user. The historical backtest assumes each preceding report was available before the next auction because the CSV has auction dates and no publication timestamps.

Dataset by Mallawarachchi et al. [Colombo Tea Auction dataset](https://huggingface.co/datasets/colombo-tea-auction-prices/cta-price-prediction), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The exported assets include derived group descriptors, model predictions and evaluation results. OpenAI Codex assisted with implementation and verification.
