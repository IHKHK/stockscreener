import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import yfinance as yf

DATA_DIR = Path("data")
CONSTITUENTS_FILE = DATA_DIR / "constituents.json"
OUTPUT_FILE = DATA_DIR / "breadth.json"
MA_WINDOWS = [10, 50, 150, 250]
BENCHMARK_SYMBOL = "2800.HK"
STRENGTH_WEIGHTS = {"ma10": 0.20, "ma50": 0.40, "ma150": 0.25, "ma250": 0.15}

def load_constituents():
    return json.loads(CONSTITUENTS_FILE.read_text(encoding="utf-8"))

def get_close_panel(symbols):
    df = yf.download(symbols, period="3y", interval="1d", auto_adjust=True, group_by="ticker", progress=False, threads=True)
    if df.empty:
        raise RuntimeError("No price data downloaded.")
    close_map = {}
    for symbol in symbols:
        try:
            if isinstance(df.columns, pd.MultiIndex):
                close = df[(symbol, "Close")].dropna()
            else:
                close = df["Close"].dropna()
            if not close.empty:
                close_map[symbol] = close
        except Exception:
            print(f"[WARN] Missing close data: {symbol}")
    if not close_map:
        raise RuntimeError("No usable close series.")
    return pd.DataFrame(close_map).sort_index()

def calc_breadth(close_panel, constituents):
    symbols = [x["symbol"] for x in constituents]
    sectors = {x["symbol"]: x["sector"] for x in constituents}
    above = {}
    for win in MA_WINDOWS:
        above[win] = close_panel > close_panel.rolling(win).mean()
    breadth_rows = []
    sector_rows = []
    sector_names = sorted(set(sectors.values()))
    for dt in close_panel.index:
        row = {"date": dt.strftime("%Y-%m-%d")}
        for win in MA_WINDOWS:
            valid = above[win].loc[dt, symbols].dropna()
            row[f"ma{win}"] = float(valid.mean() * 100) if len(valid) else None
        row["validCount"] = int(above[50].loc[dt, symbols].dropna().shape[0])
        breadth_rows.append(row)
        for sector in sector_names:
            sector_symbols = [s for s in symbols if sectors[s] == sector]
            srow = {"date": dt.strftime("%Y-%m-%d"), "sector": sector, "count": len(sector_symbols)}
            for win in MA_WINDOWS:
                valid = above[win].loc[dt, sector_symbols].dropna()
                srow[f"ma{win}"] = float(valid.mean() * 100) if len(valid) else None
            keys = ["ma10", "ma50", "ma150", "ma250"]
            if all(srow.get(k) is not None for k in keys):
                srow["strengthScore"] = sum(srow[k] * STRENGTH_WEIGHTS[k] for k in keys)
            else:
                srow["strengthScore"] = None
            sector_rows.append(srow)
    return breadth_rows, sector_rows

def calc_benchmark():
    df = yf.download(BENCHMARK_SYMBOL, period="3y", interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        return []
    close = df["Close"].dropna()
    normalized = 50 + ((close / close.shift(100)) - 1) * 100
    return [{"date": dt.strftime("%Y-%m-%d"), "symbol": BENCHMARK_SYMBOL, "value": float(v)} for dt, v in normalized.dropna().items()]

def main():
    DATA_DIR.mkdir(exist_ok=True)
    constituents = load_constituents()
    symbols = [x["symbol"] for x in constituents]
    print(f"Downloading {len(symbols)} HK stocks...")
    close_panel = get_close_panel(symbols)
    print("Calculating breadth...")
    breadth_rows, sector_rows = calc_breadth(close_panel, constituents)
    print("Downloading 2800 benchmark...")
    benchmark_rows = calc_benchmark()
    latest_sector = {}
    if sector_rows:
        latest_date = sector_rows[-1]["date"]
        latest_sector = {
            "date": latest_date,
            "items": sorted([r for r in sector_rows if r["date"] == latest_date], key=lambda x: x["strengthScore"] if x["strengthScore"] is not None else -1, reverse=True),
        }
    output = {
        "updatedAt": datetime.now().isoformat(timespec="seconds"),
        "universe": {"name": "HK 39 Blue Chips MVP", "stockCount": len(constituents), "benchmark": BENCHMARK_SYMBOL},
        "constituents": constituents,
        "breadth": breadth_rows,
        "sectors": sector_rows,
        "latestSectorStrength": latest_sector,
        "benchmark": benchmark_rows,
    }
    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
