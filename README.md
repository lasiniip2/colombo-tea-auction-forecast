# Colombo Tea Auction Forecast

This Flask dashboard forecasts the next Colombo Tea Auction price midpoint in Sri Lankan rupees. It compares five standalone ensemble models and a Random Forest + XGBoost stack against the last-price benchmark.

## Run locally

Use **Python 3.12** and run these commands from the project folder.

```sh
python -m pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The Flask app loads fitted preprocessing and models from `dashboard_assets/`. Run `train_and_compare.ipynb` with the source CSV to reproduce the experiment and regenerate the assets.

## Test results and scope

The nine inputs are seven tea descriptors, the month of the upcoming auction, and the last published midpoint. Each model estimates how much the price will change. The backtest uses 1,764 matched quotations across 17 reserved auctions. The last-price benchmark had the lowest MAE (**LKR 36.05**), and the stack led the ML models (**LKR 36.74**). The **Model comparison** page shows MAE, RMSE, R², the percentage of predictions within LKR 50, and a filterable predicted-versus-recorded chart.

The estimate describes a broker quotation group. It uses the latest midpoint supplied by the user. The historical backtest assumes each preceding report was available before the next auction because the CSV has auction dates and no publication timestamps.

Dataset by Mallawarachchi et al. [Colombo Tea Auction dataset](https://huggingface.co/datasets/colombo-tea-auction-prices/cta-price-prediction), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The exported assets include derived group descriptors, model predictions and evaluation results. OpenAI Codex assisted with implementation and verification.

A machine learning assignment by **Lasini Pallewaththa**.
