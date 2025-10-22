import math
import os
import argparse
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import csv

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import TwoSlopeNorm
import yfinance as yf

from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
from sklearn.inspection import permutation_importance

plt.style.use('seaborn-v0_8-darkgrid')

# --------------------------------------------------------------------------------------
# Konfiguration (wird in main() mit CLI-Parametern überschrieben)
# --------------------------------------------------------------------------------------
PROFILE = "aggressive"  # "balanced" | "aggressive"

PROFILES = {
    "balanced": dict(
        SYMBOL="QQQ",                     # wird in main() überschrieben, Default Nasdaq-ETF
        DAILY_PERIOD="10y",
        H1_PERIOD="730d",
        M30_PERIOD="60d",
        START_CAPITAL=100_000.0,
        RISK_PER_TRADE=0.01,
    # Dynamische Risiko / Risikosteuerung
    DYNAMIC_DD_RISK=True,               # Passe Risiko bei Drawdowns an
    DD_RISK_STEPS=[(-10,0.75),(-20,0.5),(-30,0.35),(-40,0.25)],  # (Drawdown %, Multiplikator)
    USE_VOL_TARGET=False,               # Annualisierte Vol-Zielsteuerung aktiv?
    TARGET_ANNUAL_VOL=0.25,             # Ziel-Vol (25%)
    VOL_WINDOW_TRADES=40,               # Rolling Fenster über Trades
    RISK_PER_TRADE_MIN=0.002,           # Untere Klammer für dynamisches Risiko
    RISK_PER_TRADE_MAX=0.02,            # Obere Klammer
    MAX_DRAWDOWN_STOP=-60.0,            # Stop Trading wenn Equity DD < -60%
    OPTIMIZE_ML_THRESHOLD=True,         # Finde bestes Probability-Threshold
        ATR_PERIOD=14,
    ATR_MULT_BUFFER=0.25,
    # Asymmetrische Defaults (Fallbacks, können überschrieben werden)
    TP1_LONG=1.272, TP2_LONG=1.618,
    TP1_SHORT=1.272, TP2_SHORT=1.618,
    ATR_MULT_BUFFER_LONG=0.25,
    ATR_MULT_BUFFER_SHORT=0.25,
    ENTRY_ZONE_W3_LONG=(0.50, 0.786),
    ENTRY_ZONE_W3_SHORT=(0.50, 0.786),
    ENTRY_ZONE_W5_LONG=(0.236, 0.50),
    ENTRY_ZONE_W5_SHORT=(0.236, 0.50),
    ENTRY_ZONE_C_LONG=(0.50, 0.786),
    ENTRY_ZONE_C_SHORT=(0.50, 0.786),
        # Struktur-Engines
        PRIMARY_ZZ_PCT=0.013, PRIMARY_ZZ_ATR_MULT=1.00, PRIMARY_MIN_IMP_ATR=2.2,   # Daily (Plot)
        H1_ZZ_PCT=0.0030,  H1_ZZ_ATR_MULT=0.80,  H1_MIN_IMP_ATR=2.0,               # 1H (Trading)
        # Entries / Targets
        ENTRY_ZONE_W3=(0.50, 0.786),
        ENTRY_ZONE_W5=(0.236, 0.50),
        ENTRY_ZONE_C=(0.50, 0.786),
        ENTRY_WINDOW_H1=72,
        ENTRY_WINDOW_M30=144,
        MAX_HOLD_H1=144,
        MAX_HOLD_M30=288,
        TP1=1.272, TP2=1.618,
        # Filter
        EMA_FAST=50, EMA_SLOW=200,
    USE_EMA_TREND=False,  # deaktiviert (User Wunsch: EMA Trend aus)
        REQUIRE_PRICE_ABOVE_EMA_FAST=False,  # gelockert -> mehr Trades
        USE_DAILY_EMA=True,
    ATR_PCT_MIN=0.06, ATR_PCT_MAX=2.00,  # niedrigeres Minimum
    # Regime-Filter (ADX)
    ADX_TREND_THRESHOLD=25,
    USE_ADX=True,
        # Confirmation
        REQUIRE_CONFIRM=True,
        CONFIRM_BARS_H1=5, CONFIRM_BARS_M30=10,
        CONFIRM_RULES=("break_prev_extreme", "ema_fast_cross"),
        ALLOW_TOUCH_IF_NO_CONFIRM=True,      # gelockert
        # ML + Guards
        USE_ML=True, TRAIN_FRAC=0.6, CALIBRATE_PROBS=True,
        SIZE_BY_PROB=True, PROB_SIZE_MIN=0.7, PROB_SIZE_MAX=1.4,
        ML_MIN_PASS_RATE=0.30,               # mind. 30% der Signale passieren im Train
        ML_MIN_PASS_RATE_TEST=0.25,          # und im Test
    # Trades
        USE_W5=False,
    SIZE_SHORT_FACTOR=0.75,
    # Kosten (nicht verwendet in Original-Baseline)
    COMMISSION_PER_TRADE=0.0,
    SLIPPAGE_PCT=0.0,
        # Plot / Struktur
        SHOW_INTERMEDIATE=True,
        LABEL_GAP_DAYS=25,
    PLOT_TRADE_SAMPLE=200,
    # Neue Plot-/Filter-Parameter
    EQUITY_LOG_THRESHOLD=5.0,           # Faktor (Range/Min) ab dem log-Skala verwendet wird
    WAVE_MIN_PCT=0.08,                  # Mindestbewegung (relativ zum Preis) für Anzeige Primary
    WAVE_MIN_DURATION_DAYS=40,          # Mindestdauer in Tagen für Anzeige Primary
    WAVE_LABEL_GAP_DAYS=60,             # Lücke zwischen Labels
    # Portfolio Not‑Stopp (nicht verwendet in Original-Baseline)
    MAX_PORTFOLIO_DD=-1e9
    ),
    "aggressive": dict(
        SYMBOL="^GSPC",            # alte Basis
        DAILY_PERIOD="10y",
        H1_PERIOD="730d",
        M30_PERIOD="60d",
        START_CAPITAL=100_000.0,
        RISK_PER_TRADE=0.01,
        ATR_PERIOD=14,
        ATR_MULT_BUFFER=0.20,
        PRIMARY_ZZ_PCT=0.012, PRIMARY_ZZ_ATR_MULT=0.90, PRIMARY_MIN_IMP_ATR=1.8,
        H1_ZZ_PCT=0.0020,  H1_ZZ_ATR_MULT=0.60,  H1_MIN_IMP_ATR=1.6,
        ENTRY_ZONE_W3=(0.382, 0.786),
        ENTRY_ZONE_W5=(0.236, 0.618),
        ENTRY_ZONE_C=(0.382, 0.786),
        ENTRY_WINDOW_H1=96,
        ENTRY_WINDOW_M30=192,
        MAX_HOLD_H1=192,
        MAX_HOLD_M30=384,
        TP1=1.272, TP2=1.618,
        EMA_FAST=34, EMA_SLOW=144,
        USE_EMA_TREND=False,        # wie gewünscht ausgeschaltet
        REQUIRE_PRICE_ABOVE_EMA_FAST=False,
        USE_DAILY_EMA=False,
        ATR_PCT_MIN=0.05, ATR_PCT_MAX=2.50,
        REQUIRE_CONFIRM=True,
        CONFIRM_BARS_H1=6, CONFIRM_BARS_M30=12,
        CONFIRM_RULES=("break_prev_extreme","ema_fast_cross"),
        ALLOW_TOUCH_IF_NO_CONFIRM=True,
        USE_ML=True, TRAIN_FRAC=0.6, CALIBRATE_PROBS=True,
        SIZE_BY_PROB=True, PROB_SIZE_MIN=0.7, PROB_SIZE_MAX=1.5,
        ML_MIN_PASS_RATE=0.30,
        ML_MIN_PASS_RATE_TEST=0.25,
        USE_W5=False,
        SIZE_SHORT_FACTOR=0.7,
        SHOW_INTERMEDIATE=True,
        LABEL_GAP_DAYS=25,
        PLOT_TRADE_SAMPLE=220,
        EQUITY_LOG_THRESHOLD=5.0,
        WAVE_MIN_PCT=0.08,
        WAVE_MIN_DURATION_DAYS=40,
        WAVE_LABEL_GAP_DAYS=60,
        MAX_PORTFOLIO_DD=-1e9
    ),
    "adaptive": dict(
        SYMBOL="QQQ",
        DAILY_PERIOD="10y",
        H1_PERIOD="730d",
        M30_PERIOD="60d",
        START_CAPITAL=100_000.0,
        RISK_PER_TRADE=0.008,              # 0.8%
        DYNAMIC_DD_RISK=True,
        DD_RISK_STEPS=[(-5,0.85),(-10,0.65),(-15,0.50),(-20,0.38),(-25,0.30)],
        USE_VOL_TARGET=True,
        TARGET_ANNUAL_VOL=0.25,
        VOL_WINDOW_TRADES=35,
        RISK_PER_TRADE_MIN=0.002,
        RISK_PER_TRADE_MAX=0.012,
        MAX_DRAWDOWN_STOP=-40.0,
        OPTIMIZE_ML_THRESHOLD=True,
        ATR_PERIOD=14,
        ATR_MULT_BUFFER=0.20,
        TP1_LONG=1.272, TP2_LONG=1.618,
        TP1_SHORT=1.272, TP2_SHORT=1.618,
        ATR_MULT_BUFFER_LONG=0.20,
        ATR_MULT_BUFFER_SHORT=0.20,
        ENTRY_ZONE_W3_LONG=(0.382, 0.786),
        ENTRY_ZONE_W3_SHORT=(0.50, 0.786),
        ENTRY_ZONE_W5_LONG=(0.236, 0.618),
        ENTRY_ZONE_W5_SHORT=(0.382, 0.618),
        ENTRY_ZONE_C_LONG=(0.382, 0.786),
        ENTRY_ZONE_C_SHORT=(0.50, 0.786),
        PRIMARY_ZZ_PCT=0.012, PRIMARY_ZZ_ATR_MULT=0.90, PRIMARY_MIN_IMP_ATR=1.9,
        H1_ZZ_PCT=0.0022,  H1_ZZ_ATR_MULT=0.60, H1_MIN_IMP_ATR=1.7,
        ENTRY_ZONE_W3=(0.382, 0.786),
        ENTRY_ZONE_W5=(0.236, 0.618),
        ENTRY_ZONE_C=(0.382, 0.786),
        ENTRY_WINDOW_H1=96,
        ENTRY_WINDOW_M30=192,
        MAX_HOLD_H1=192,
        MAX_HOLD_M30=384,
        TP1=1.272, TP2=1.618,
        EMA_FAST=34, EMA_SLOW=144,
        USE_EMA_TREND=True,
        REQUIRE_PRICE_ABOVE_EMA_FAST=False,
        USE_DAILY_EMA=False,   # deaktiviert (geringer Zusatznutzen)
        ATR_PCT_MIN=0.05, ATR_PCT_MAX=2.30,
        ADX_TREND_THRESHOLD=25,
        USE_ADX=False,         # ADX aus (keine Filterwirkung festgestellt)
        REQUIRE_CONFIRM=True,
        CONFIRM_BARS_H1=6, CONFIRM_BARS_M30=12,
        CONFIRM_RULES=("break_prev_extreme", "ema_fast_cross"),
        ALLOW_TOUCH_IF_NO_CONFIRM=True,
        USE_ML=True, TRAIN_FRAC=0.6, CALIBRATE_PROBS=True,
        SIZE_BY_PROB=True, PROB_SIZE_MIN=0.8, PROB_SIZE_MAX=1.35,
        ML_MIN_PASS_RATE=0.30,
        ML_MIN_PASS_RATE_TEST=0.25,
        USE_W5=False,
        SIZE_SHORT_FACTOR=0.6,
        COMMISSION_PER_TRADE=0.0,
        SLIPPAGE_PCT=0.0,
        SHOW_INTERMEDIATE=True,
        LABEL_GAP_DAYS=25,
        PLOT_TRADE_SAMPLE=220,
        EQUITY_LOG_THRESHOLD=5.0,
        WAVE_MIN_PCT=0.08,
        WAVE_MIN_DURATION_DAYS=40,
        WAVE_LABEL_GAP_DAYS=60,
        MAX_PORTFOLIO_DD=-1e9
    ),
}

# Wird in main() gesetzt (damit wir Symbol/Profil einfach überschreiben können)
CFG: Dict = {}
RISK_FREE_RATE = 2.0  # % p.a.

# --------------------------------------------------------------------------------------
# Data & Indicators
# --------------------------------------------------------------------------------------
def _normalize_yf_df(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    # Flatten MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join([str(x) for x in tup if x and x!='-']).strip() for tup in df.columns]
    # Normalize names
    df.columns = [str(c).strip().lower().replace('\ufeff','') for c in df.columns]
    # Ersetze Leerzeichen durch Unterstrich für robustere Erkennung
    df.columns = [c.replace(' ', '_') for c in df.columns]
    sym_lower = str(symbol).lower()
    # Dynamisches Mapping: open_xxx, close_xxx etc. auf Basisnamen reduzieren
    mapped_cols = {}
    for c in df.columns:
        base = c
        if '_' in c:
            parts = c.split('_')
            # Fälle wie close_qqq, open_qqq
            if parts[0] in {'open','high','low','close','volume'}:
                base = parts[0]
            # adj_close_qqq oder adjclose_qqq
            elif (parts[0] in {'adj','adjclose','adjclose'} or (parts[0]=='adj' and parts[1]=='close')):
                base = 'adj_close'
            elif parts[0]=='adj' and len(parts)>1 and parts[1] in {'close','cls'}:
                base='adj_close'
        # Falls yfinance Format: qqq_close -> letzte Komponente ist relevant
        if sym_lower in c and c.endswith('_close'):
            base = 'close'
        mapped_cols[c] = base
    # Anwenden des Mappings (nur wenn keine Kollision mit existierendem Namen anderer Spalte ohne Mapping)
    new_cols = []
    counts = {}
    for c in df.columns:
        b = mapped_cols.get(c,c)
        counts[b] = counts.get(b,0)+1
        if counts[b]>1 and b in {'open','high','low','close','volume','adj_close'}:
            # eindeutiger machen
            new_cols.append(f"{b}_{counts[b]}")
        else:
            new_cols.append(b)
    df.columns = new_cols
    # Fallback: erste Spalte mit 'close' im Namen nehmen
    if 'close' not in df.columns:
        cand = [c for c in df.columns if 'close' in c]
        if cand:
            df['close'] = df[cand[0]]
    # Header row misuse heuristic
    if 'close' not in df.columns and len(df)>0:
        first = [str(x).strip().lower() for x in df.iloc[0].values]
        if 'close' in first and len(set(first))==len(first):
            df.columns = first
            df = df.iloc[1:]
    # Adj close fallback
    if 'close' not in df.columns and 'adj close' in df.columns:
        df = df.rename(columns={'adj close':'close'})
    if 'close' not in df.columns and 'adj_close' in df.columns:
        df = df.rename(columns={'adj_close':'close'})
    # Date inference
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    elif 'timestamp' in df.columns:
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
    else:
        idx = df.index
        df['date'] = pd.to_datetime(idx, errors='coerce')
    keep_cols = ['date'] + [c for c in ['open','high','low','close','volume'] if c in df.columns]
    df = df[keep_cols].copy()
    # Dates tz-naiv erzwingen (verhindert spätere Vergleichsfehler)
    try:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['date'] = df['date'].dt.tz_localize(None)
    except Exception:
        try:
            df['date'] = df['date'].dt.tz_convert(None)
        except Exception:
            pass
    for c in ['open','high','low','close','volume']:
        if c in df.columns:
            try:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            except Exception:
                pass
    if 'close' not in df.columns:
        raise ValueError("CSV/DF enthält keine 'close'-Spalte! Prüfe Datei.")
    df = df.dropna(subset=['date','close']).drop_duplicates(subset=['date']).sort_values('date')
    return df.reset_index(drop=True)
    # Wenn DataFrame leer ist, sofort zurückgeben
    if df is None or df.empty or len(df.columns) == 0:
        return pd.DataFrame()
    # Versuche, alle numerischen Spalten zu konvertieren (nur falls vorhanden)
    for c in ["open", "high", "low", "close"]:
        if c in df.columns:
            col = df[c]
            # Nur konvertieren, wenn es eine Series ist und 1D
            if isinstance(col, pd.Series) and col.ndim == 1 and not col.empty:
                try:
                    df[c] = pd.to_numeric(col, errors='coerce')
                except Exception:
                    pass
    # Spaltennamen normalisieren: trim, lower, unsichtbare Zeichen entfernen
    df.columns = [str(c).strip().lower().replace('\ufeff','').replace('"','').replace("'","") for c in df.columns]
    # Falls alles in einer Spalte: versuche, die erste Zeile als Header zu nehmen
    if len(df.columns) == 1 and ',' in df.columns[0]:
        df = df[df.columns[0]].str.split(',', expand=True)
        df.columns = [str(c).strip().lower() for c in df.iloc[0]]
        df = df.drop(df.index[0]).reset_index(drop=True)
    # Nochmals Spaltennamen normalisieren
    df.columns = [str(c).strip().lower().replace('\ufeff','').replace('"','').replace("'","") for c in df.columns]
    # RADIKALER FALLBACK: Wenn immer noch keine 'close'-Spalte, prüfe, ob die erste Zeile die Header ist
    if 'close' not in df.columns:
        # Prüfe, ob die erste Zeile wie ein Header aussieht (z.B. 'timestamp', 'open', ...)
        first_row = [str(x).strip().lower() for x in df.iloc[0].values]
        if 'close' in first_row:
            df.columns = first_row
            df = df.drop(df.index[0]).reset_index(drop=True)
        # Nochmals normalisieren
        df.columns = [str(c).strip().lower().replace('\ufeff','').replace('"','').replace("'","") for c in df.columns]
    # Wenn immer noch nicht: explizite Fehlermeldung
    if 'close' not in df.columns:
        raise ValueError("CSV/DF enthält keine 'close'-Spalte! Prüfe die Datei und Spaltennamen.")
    # Timestamp/Date konvertieren
    if 'timestamp' in df.columns:
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    elif df.index.name in ['date','timestamp']:
        df['date'] = pd.to_datetime(df.index, errors='coerce')
    else:
        # Fallback: versuche, die erste Spalte als Datum zu interpretieren
        try:
            df['date'] = pd.to_datetime(df.iloc[:,0], errors='coerce')
        except Exception:
            pass
    return df
def robust_read_csv(path):
    # Versuche, das Trennzeichen automatisch zu erkennen
    with open(path, 'r', encoding='utf-8-sig') as f:
        sample = f.read(2048)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
            sep = dialect.delimiter
        except Exception:
            sep = ','
    df = pd.read_csv(path, sep=sep, engine='python')
    # Wenn alles in einer Spalte steht, splitte manuell
    if len(df.columns) == 1 and sep in df.columns[0]:
        df = pd.read_csv(path, sep=sep, engine='python')
    if len(df.columns) == 1:
        # Fallback: splitte per Komma
        df = df[df.columns[0]].str.split(',', expand=True)
        df.columns = df.iloc[0]
        df = df.drop(df.index[0]).reset_index(drop=True)
    return df

def _make_tz_naive(series: pd.Series) -> pd.Series:
    try:
        return series.dt.tz_localize(None)
    except Exception:
        try:
            return series.dt.tz_convert(None)
        except Exception:
            return series

def _merge_history(symbol:str, cur:pd.DataFrame, hist_path:str) -> pd.DataFrame:
    if cur is None or cur.empty:
        cur = pd.DataFrame()
    if not os.path.exists(hist_path):
        return cur
    try:
        raw = robust_read_csv(hist_path)
        old = _normalize_yf_df(raw, symbol)
        if not old.empty:
            # Zeitzonen vereinheitlichen
            if 'date' in old.columns:
                old['date'] = _make_tz_naive(pd.to_datetime(old['date'], errors='coerce'))
            if 'date' in cur.columns:
                cur['date'] = _make_tz_naive(pd.to_datetime(cur['date'], errors='coerce'))
            merged = pd.concat([old, cur], ignore_index=True)
            merged = merged.dropna(subset=['date']).drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
            return merged
    except Exception as e:
        print(f"[WARN] Merge {os.path.basename(hist_path)}: {e}")
    return cur

def load_data():
    sym = CFG["SYMBOL"]
    print(f"[{CFG['_PROFILE']}] Lade {sym}: Daily={CFG['DAILY_PERIOD']} | 1H={CFG['H1_PERIOD']} | 30m={CFG['M30_PERIOD']}")
    if CFG.get("USE_CSV", False):
        print("[CSV] Lade Kursdaten aus CSV...")
        base = os.path.dirname(__file__)
        sym_sanit = sym.replace('=','_').replace('^','')
        # Kandidatenlisten (verschiedene Namensschemata und Ordner)
        def _candidates(prefix: str):
            core = [
                f"{prefix}_{sym}.csv",
                f"{prefix}_{sym_sanit}.csv",
                f"{sym}_{prefix}.csv",
                f"{sym_sanit}_{prefix}.csv",
                f"{prefix}.csv",
                f"{sym}.csv",
                f"{sym_sanit}.csv",
            ]
            # Duplikate entfernen, Reihenfolge beibehalten
            seen, uniq = set(), []
            for x in core:
                if x not in seen:
                    seen.add(x); uniq.append(x)
            paths = []
            for folder in [base, os.path.join(base, 'daten')]:
                for fname in uniq:
                    paths.append(os.path.join(folder, fname))
            return paths
        if sym == "EURUSD=X":
            # Spezielle bekannten Historien-Dateien
            daily_candidates = [os.path.join(base, "daten", "eurusd-d1-bid-1988-01-15-2025-09-07.csv")] + _candidates("daily")
            h1_candidates    = [os.path.join(base, "daten", "eurusd-h1-bid-2003-05-04T21-2025-09-07.csv")] + _candidates("h1")
            # M30 Pattern-Suche ergänzend zu Standard-Kandidaten
            m30_candidates = []
            for folder in [base, os.path.join(base, 'daten')]:
                if os.path.isdir(folder):
                    for fn in os.listdir(folder):
                        low = fn.lower()
                        if low.startswith('eurusd-m30-bid-') and low.endswith('.csv'):
                            m30_candidates.append(os.path.join(folder, fn))
            m30_candidates += _candidates("m30")
        else:
            daily_candidates = _candidates("daily")
            h1_candidates    = _candidates("h1")
            m30_candidates   = _candidates("m30")
        def _select(label, candidates):
            existing = [p for p in candidates if os.path.exists(p)]
            print(f"[CSV-TRY] {label} Kandidaten (erste 8 gezeigt):")
            for p in candidates[:8]:
                print(f"   - {p} {'(OK)' if os.path.exists(p) else ''}")
            return existing[0] if existing else candidates[0]
        daily_path = _select('Daily', daily_candidates)
        h1_path    = _select('H1', h1_candidates)
        m30_path   = _select('M30', m30_candidates)
        # Debug Pfade + Existenz
        def _pinfo(label, path):
            if not path:
                print(f"[CSV-PATH] {label}: (None)")
                return
            exists = os.path.exists(path)
            size = os.path.getsize(path) if exists else 0
            print(f"[CSV-PATH] {label}: {path} | exists={exists} | size={size}B")
        _pinfo('Daily', daily_path)
        _pinfo('H1', h1_path)
        _pinfo('M30', m30_path)
        # Einlesen nur wenn vorhanden
        daily = robust_read_csv(daily_path) if os.path.exists(daily_path) else pd.DataFrame()
        h1    = robust_read_csv(h1_path)    if os.path.exists(h1_path)    else pd.DataFrame()
        m30   = robust_read_csv(m30_path)   if os.path.exists(m30_path)   else pd.DataFrame()
        print(f"[CSV-RAW] daily shape={daily.shape} | h1 shape={h1.shape} | m30 shape={m30.shape}")
        daily = _normalize_yf_df(daily, sym) if not daily.empty else pd.DataFrame()
        h1    = _normalize_yf_df(h1, sym)    if not h1.empty    else pd.DataFrame()
        m30   = _normalize_yf_df(m30, sym)   if not m30.empty   else pd.DataFrame()
        print(f"[CSV-NORM] daily shape={daily.shape} | h1 shape={h1.shape} | m30 shape={m30.shape}")
        # Helper für Fallbacks
        def _yf(period, interval, _sym=sym):
            try:
                raw = yf.download(_sym, period=period, interval=interval, auto_adjust=True, group_by="column", progress=False)
                return _normalize_yf_df(raw, _sym)
            except Exception as e:
                print(f"[WARN] yfinance Fallback {interval} fehlgeschlagen: {e}")
                return pd.DataFrame()
        if daily.empty:
            print("[FALLBACK] daily CSV fehlt/leer -> lade von yfinance")
            daily = _yf(CFG['DAILY_PERIOD'], '1d')
        if h1.empty:
            print("[FALLBACK] h1 CSV fehlt/leer -> lade von yfinance")
            h1 = _yf(CFG['H1_PERIOD'], '1h')
        if m30.empty:
            print("[INFO] Keine m30 Daten (CSV leer/fehlend). Verwende nur 1H für Entries.")
        daily, h1, m30 = add_all_indicators(daily, h1, m30)
        for nm, dfx in [("Daily", daily), ("H1", h1), ("M30", m30)]:
            if not dfx.empty and 'date' in dfx.columns:
                try:
                    print(f"[SPAN] {nm}: {dfx['date'].iloc[0].date()} -> {dfx['date'].iloc[-1].date()} ({len(dfx)} Zeilen)")
                except Exception:
                    pass
        # Wenn Daily oder H1 nach Fallback immer noch leer -> Abbruch
        if daily.empty or h1.empty:
            print("[ERROR] Kritische Zeitreihe leer (Daily oder H1). Bitte CSV prüfen oder Internetverbindung für yfinance sicherstellen.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        return daily, h1, m30
    else:
        # Erst yfinance ziehen (begrenzter Zeitraum)
        d = yf.download(sym, period=CFG["DAILY_PERIOD"], interval="1d",  auto_adjust=True, group_by="column", progress=False)
        h = yf.download(sym, period=CFG["H1_PERIOD"],   interval="1h",  auto_adjust=True, group_by="column", progress=False)
        m = yf.download(sym, period=CFG["M30_PERIOD"],  interval="30m", auto_adjust=True, group_by="column", progress=False)
        d = _normalize_yf_df(d, sym)
        h = _normalize_yf_df(h, sym)
        m = _normalize_yf_df(m, sym)
        # Automatischer Merge für bekannte FX-Historien (kompakt)
        if sym == "EURUSD=X":
            base = os.path.dirname(__file__)
            d = _merge_history(sym, d, os.path.join(base, "daten", "eurusd-d1-bid-1988-01-15-2025-09-07.csv"))
            h = _merge_history(sym, h, os.path.join(base, "daten", "eurusd-h1-bid-2003-05-04T21-2025-09-07.csv"))
            # M30: flexible Pattern-Suche (weil Datei evtl. im Unterordner 'daten' oder Root liegt)
            m30_candidates = []
            for folder in [base, os.path.join(base, 'daten')]:
                if os.path.isdir(folder):
                    for fn in os.listdir(folder):
                        if fn.lower().startswith('eurusd-m30-bid-') and fn.lower().endswith('.csv'):
                            m30_candidates.append(os.path.join(folder, fn))
            if m30_candidates:
                # Älteste Datei (frühestes Datum im Dateinamen heuristisch über Länge / sort) zuerst
                m30_candidates.sort()
                hist_m30_path = m30_candidates[0]
                m = _merge_history(sym, m, hist_m30_path)
        # Indikatoren
        d, h, m = add_all_indicators(d, h, m)
        # Einheitlich TZ-naiv (Sicherheitsnetz gegen Mischformen)
        for df_ref in (d,h,m):
            if not df_ref.empty and 'date' in df_ref.columns:
                try:
                    df_ref['date'] = pd.to_datetime(df_ref['date'], errors='coerce').dt.tz_localize(None)
                except Exception:
                    try:
                        df_ref['date'] = pd.to_datetime(df_ref['date'], errors='coerce').dt.tz_convert(None)
                    except Exception:
                        pass
        # Debug-Spanne
        for nm,df in [("Daily",d),("H1",h),("M30",m)]:
            if not df.empty:
                print(f"[SPAN] {nm}: {df['date'].iloc[0].date()} -> {df['date'].iloc[-1].date()} ({len(df)} Zeilen)")
        return d, h, m

def add_indicators(df: pd.DataFrame):
    if df.empty:
        return df
    # Ensure 'close' exists
    if "close" not in df.columns:
        if "adj_close" in df.columns:
            df["close"] = df["adj_close"]
        elif "Close" in df.columns:
            df["close"] = df["Close"]
        else:
            df["close"] = np.nan
    # Ensure 'high' and 'low' exist
    if "high" not in df.columns:
        if "High" in df.columns:
            df["high"] = df["High"]
        else:
            df["high"] = df["close"]
    if "low" not in df.columns:
        if "Low" in df.columns:
            df["low"] = df["Low"]
        else:
            df["low"] = df["close"]
    # Now calculate indicators robustly
    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")
    prev = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev).abs(), (low - prev).abs()], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(CFG.get("ATR_PERIOD", 14), min_periods=1).mean()
    df["ATR_PCT"] = (df["ATR"] / close) * 100.0
    df["EMA_FAST"] = close.ewm(span=CFG.get("EMA_FAST", 21), adjust=False).mean()
    df["EMA_SLOW"] = close.ewm(span=CFG.get("EMA_SLOW", 55), adjust=False).mean()
    # RSI (Feature)
    delta = close.diff().fillna(0.0)
    up = delta.clip(lower=0).rolling(14).mean()
    down = (-delta.clip(upper=0)).rolling(14).mean()
    rs = up / (down + 1e-12)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def add_all_indicators(daily: pd.DataFrame, h1: pd.DataFrame, m30: pd.DataFrame):
    daily = add_indicators(daily)
    h1 = add_indicators(h1)
    m30 = add_indicators(m30)
    return daily, h1, m30

# Einfacher ADX(14)-Berechner (Fallback, falls pandas_ta nicht verfügbar)
def compute_adx(df: pd.DataFrame, n: int = 14, out_col: str = "ADX_14"):
    if df.empty or not {"high","low","close"}.issubset(df.columns):
        return
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)
    up = high - prev_high
    down = prev_low - low
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = pd.concat([(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0/n, adjust=False).mean()
    plus_di = 100.0 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1.0/n, adjust=False).mean() / (atr + 1e-12))
    minus_di = 100.0 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1.0/n, adjust=False).mean() / (atr + 1e-12))
    dx = 100.0 * ((plus_di - minus_di).abs() / ((plus_di + minus_di).abs() + 1e-12))
    adx = dx.ewm(alpha=1.0/n, adjust=False).mean()
    df[out_col] = adx

# --------------------------------------------------------------------------------------
# Elliott Engines
# --------------------------------------------------------------------------------------
class Dir(Enum):
    UP=1; DOWN=2

@dataclass
class Pivot:
    idx:int; price:float; kind:str  # 'H'/'L'

@dataclass
class Impulse:
    direction:Dir; points:List[Pivot]  # [p0..p5]

@dataclass
class ABC:
    direction:Dir; points:List[Pivot]  # [A0,A1,B1,C1]

class ElliottEngine:
    def __init__(self, zz_pct:float, zz_atr_mult:float, min_impulse_atr:float):
        self.zz_pct = zz_pct; self.zz_atr_mult = zz_atr_mult; self.min_imp = min_impulse_atr

    @staticmethod
    def _thr(base:float, atr:float, pct:float, atr_mult:float)->float:
        if pd.isna(atr): return base*pct
        return max(base*pct, atr*atr_mult)

    def zigzag(self, close:np.ndarray, atr:np.ndarray)->List[Pivot]:
        piv=[]
        if len(close)<3: return piv
        last=close[0]; hi=last; lo=last; hi_i=0; lo_i=0; direction=None
        for i in range(1,len(close)):
            p=close[i]
            thr=self._thr(last, atr[i] if atr is not None and i<len(atr) else np.nan, self.zz_pct, self.zz_atr_mult)
            if direction in (None, Dir.UP):
                if p>hi: hi=p; hi_i=i
                if hi-p>=thr:
                    piv.append(Pivot(hi_i,float(hi),'H')); last=hi; lo=p; lo_i=i; direction=Dir.DOWN
            if direction in (None, Dir.DOWN):
                if p<lo: lo=p; lo_i=i
                if p-lo>=thr:
                    piv.append(Pivot(lo_i,float(lo),'L')); last=lo; hi=p; hi_i=i; direction=Dir.UP
        piv.sort(key=lambda x:x.idx)
        cleaned=[]
        for p in piv:
            if not cleaned or cleaned[-1].kind!=p.kind:
                cleaned.append(p)
            else:
                if (p.kind=='H' and p.price>=cleaned[-1].price) or (p.kind=='L' and p.price<=cleaned[-1].price):
                    cleaned[-1]=p
        return cleaned

    def detect_impulses(self, piv:List[Pivot], close:np.ndarray, atr:np.ndarray)->List[Impulse]:
        res=[]; i=0
        while i<=len(piv)-6:
            s=piv[i:i+6]; kinds=''.join(p.kind for p in s)
            if kinds=='LHLHLH':
                p0,p1,p2,p3,p4,p5=s
                w1=p1.price-p0.price; w3=p3.price-p2.price
                if p2.price<=p0.price or w1<=0 or w3<0.6*w1: i+=1; continue
                if p4.price<=p1.price*0.98: i+=1; continue
                atr_b=atr[min(p3.idx, len(atr)-1)]
                if atr_b>0 and (w3/atr_b)<self.min_imp: i+=1; continue
                res.append(Impulse(Dir.UP,[p0,p1,p2,p3,p4,p5])); i+=3
            elif kinds=='HLHLHL':
                p0,p1,p2,p3,p4,p5=s
                w1=p0.price-p1.price; w3=p2.price-p3.price
                if p2.price>=p0.price or w1<=0 or w3<0.6*w1: i+=1; continue
                if p4.price>=p1.price*1.02: i+=1; continue
                atr_b=atr[min(p3.idx, len(atr)-1)]
                if atr_b>0 and (abs(w3)/atr_b)<self.min_imp: i+=1; continue
                res.append(Impulse(Dir.DOWN,[p0,p1,p2,p3,p4,p5])); i+=3
            else:
                i+=1
        return res

    def detect_abcs(self, piv:List[Pivot])->List[ABC]:
        out=[]; i=0
        while i<=len(piv)-4:
            s=piv[i:i+4]; kinds=''.join(p.kind for p in s)
            if kinds=='HLHL':
                h0,l1,h1,l2=s
                A=h0.price-l1.price; B=h1.price-l1.price
                if A<=0 or not (0.3<=B/A<=0.86) or not (l2.price<l1.price): i+=1; continue
                out.append(ABC(Dir.DOWN,[h0,l1,h1,l2])); i+=2
            elif kinds=='LHLH':
                l0,h1,l1,h2=s
                A=h1.price-l0.price; B=h1.price-l1.price
                if A<=0 or not (0.3<=B/A<=0.86) or not (h2.price>h1.price): i+=1; continue
                out.append(ABC(Dir.UP,[l0,h1,l1,h2])); i+=2
            else:
                i+=1
        return out

    @staticmethod
    def fib_zone(A:float,B:float,d:Dir,zone:Tuple[float,float])->Tuple[float,float]:
        lo,hi=sorted(zone)
        if d==Dir.UP:
            L=B-A; zL=B-L*hi; zH=B-L*lo
        else:
            L=A-B; zL=B+L*lo; zH=B+L*hi
        return (min(zL,zH),max(zL,zH))

    @staticmethod
    def fib_ext(A:float,B:float,d:Dir,ext:float)->float:
        return B+(B-A)*(ext-1.0) if d==Dir.UP else B-(A-B)*(ext-1.0)

# --------------------------------------------------------------------------------------
# Strategy types
# --------------------------------------------------------------------------------------
@dataclass
class Setup:
    setup:str; direction:Dir; start_time:pd.Timestamp; entry_tf:str
    zone:Tuple[float,float]; stop_ref:float; tp1:float; tp2:float; meta:Dict

@dataclass
class SimTrade:
    entry_tf:str; entry_idx:int; exit_idx:int
    entry:float; exit:float; per_share:float; risk_per_share:float
    setup:str; direction:str; time_in:pd.Timestamp; time_out:pd.Timestamp
    stop:float; tp1:float; tp2:float; mae_r:float; mfe_r:float
    features:Dict; label:int

@dataclass
class Trade:
    entry_tf:str; entry_idx:int; exit_idx:int
    entry:float; exit:float; pnl:float; size:int; rr:float
    setup:str; direction:str; time_in:pd.Timestamp; time_out:pd.Timestamp
    stop:float; tp1:float; tp2:float; mae_r:float; mfe_r:float
    prob:Optional[float]=None; risk_per_share:Optional[float]=None

# --------------------------------------------------------------------------------------
# Filters/Sim
# --------------------------------------------------------------------------------------
def ema_trend_ok(r:pd.Series,d:Dir)->bool:
    if not CFG["USE_EMA_TREND"]: return True
    if CFG.get("REQUIRE_PRICE_ABOVE_EMA_FAST", True):
        return (r["EMA_FAST"]>r["EMA_SLOW"] and r["close"]>r["EMA_FAST"]) if d==Dir.UP else (r["EMA_FAST"]<r["EMA_SLOW"] and r["close"]<r["EMA_FAST"])
    else:
        return (r["EMA_FAST"]>r["EMA_SLOW"]) if d==Dir.UP else (r["EMA_FAST"]<r["EMA_SLOW"])

def daily_trend_ok(daily:pd.DataFrame, ts:pd.Timestamp, d:Dir)->bool:
    if not CFG["USE_DAILY_EMA"]: return True
    idx=daily[daily["date"]<=pd.Timestamp(ts)].index
    if len(idx)==0: return True
    r=daily.loc[idx.max()]
    return (r["EMA_FAST"]>r["EMA_SLOW"]) if d==Dir.UP else (r["EMA_FAST"]<r["EMA_SLOW"])

def vol_ok(r:pd.Series)->bool:
    p=float(r["ATR_PCT"]); return CFG["ATR_PCT_MIN"]<=p<=CFG["ATR_PCT_MAX"]

def df_for_tf(h1:pd.DataFrame, m30:pd.DataFrame, tf:str)->pd.DataFrame:
    return m30 if tf=="30m" else h1

def idx_from_time(df:pd.DataFrame, ts:pd.Timestamp)->Optional[int]:
    i=df[df["date"]>=pd.Timestamp(ts)].index
    return i.min() if len(i)>0 else None

def first_touch(df:pd.DataFrame, start_ts:pd.Timestamp, zone:Tuple[float,float], window:int)->Optional[int]:
    start_i=idx_from_time(df,start_ts)
    if start_i is None: return None
    zl,zh=zone; end_i=min(start_i+window, len(df)-1)
    for i in range(start_i,end_i+1):
        lo=float(df.iloc[i]["low"]); hi=float(df.iloc[i]["high"]); cl=float(df.iloc[i]["close"])
        if (lo<=zh and hi>=zl) or (zl<=cl<=zh): return i
    return None

def confirm_idx(df:pd.DataFrame, touch_i:int, d:Dir, bars:int, allow_touch:bool)->Optional[int]:
    if not CFG["REQUIRE_CONFIRM"]: return touch_i
    end=min(touch_i+bars, len(df)-1)
    prev_hi=float(df.iloc[max(0,touch_i-1)]["high"]); prev_lo=float(df.iloc[max(0,touch_i-1)]["low"])
    for i in range(touch_i,end+1):
        r=df.iloc[i]; op=float(r["open"]); cl=float(r["close"]); ef=float(r["EMA_FAST"]); es=float(r["EMA_SLOW"])
        if "break_prev_extreme" in CFG["CONFIRM_RULES"]:
            if d==Dir.UP and cl>prev_hi: return i
            if d==Dir.DOWN and cl<prev_lo: return i
        if "ema_fast_cross" in CFG["CONFIRM_RULES"]:
            if d==Dir.UP and cl>ef and ef>es: return i
            if d==Dir.DOWN and cl<ef and ef<es: return i
    return end if allow_touch else None

def simulate(df:pd.DataFrame, entry_i:int, entry:float, d:Dir, stop:float, tp1:float, tp2:float, max_bars:int)->Tuple[int,float,float,float,float]:
    pos=1.0; realized=0.0; end=min(entry_i+max_bars, len(df)-1)
    R=abs(entry-stop); extreme=entry; mae=0.0; mfe=0.0
    for i in range(entry_i+1,end+1):
        r=df.iloc[i]; lo=float(r["low"]); hi=float(r["high"])
        if d==Dir.UP:
            extreme=max(extreme,hi); mae=min(mae,(lo-entry)/R); mfe=max(mfe,(hi-entry)/R)
            if pos==1.0 and (extreme-entry)>=R: stop=max(stop,entry)  # BE nach +1R
            if pos==1.0 and hi>=tp1:
                realized+=(tp1-entry)*0.5; pos=0.5; stop=entry
            if lo<=stop:
                realized+=(stop-entry)*pos; return i, stop, realized, mae, mfe
            if pos==0.5 and hi>=tp2:
                realized+=(tp2-entry)*0.5; return i, tp2, realized, mae, mfe
        else:
            extreme=min(extreme,lo); mae=min(mae,(entry-float(r["high"]))/R); mfe=max(mfe,(entry-lo)/R)
            if pos==1.0 and (entry-extreme)>=R: stop=min(stop,entry)
            if pos==1.0 and lo<=tp1:
                realized+=(entry-tp1)*0.5; pos=0.5; stop=entry
            if float(r["high"])>=stop:
                realized+=(entry-stop)*pos; return i, stop, realized, mae, mfe
            if pos==0.5 and lo<=tp2:
                realized+=(entry-tp2)*0.5; return i, tp2, realized, mae, mfe
    last=float(df.iloc[end]["close"])
    if d==Dir.UP:
        realized+=(last-entry)*pos; mfe=max(mfe,(last-entry)/R)
    else:
        realized+=(entry-last)*pos; mfe=max(mfe,(entry-last)/R)
    return end, last, realized, mae, mfe

# --------------------------------------------------------------------------------------
# Features (ML)
# --------------------------------------------------------------------------------------
FEATURE_COLUMNS = [
    "dir_up","setup_W3","setup_W5","setup_C",
    "atr_pct","ema_fast_slow_pct","price_above_ema_fast",
    "zone_width_pct","dist_to_zone_center_pct",
    "rsi","hour_sin","hour_cos","dow_sin","dow_cos"
]

def build_features(df: pd.DataFrame, entry_idx: int, d: Dir, setup: str, zone: Tuple[float,float]) -> Dict:
    r = df.iloc[entry_idx]
    close = float(r["close"])
    ef = float(r["EMA_FAST"]); es = float(r["EMA_SLOW"])
    atr_pct = float(r.get("ATR_PCT", 0.0))
    rsi = float(r.get("RSI", 50.0))
    ema_fast_slow_pct = (ef - es) / close if close else 0.0
    price_above_ema_fast = (close - ef) / close if close else 0.0
    zl, zh = zone
    zone_width_pct = abs(zh - zl) / close if close else 0.0
    dist_to_zone_center_pct = abs(close - (zl + zh) / 2) / close if close else 0.0
    ts = pd.Timestamp(r["date"]); hour = ts.hour + ts.minute/60.0; dow = ts.weekday()
    hour_sin = math.sin(2*math.pi*hour/24.0); hour_cos = math.cos(2*math.pi*hour/24.0)
    dow_sin = math.sin(2*math.pi*dow/7.0);     dow_cos = math.cos(2*math.pi*dow/7.0)
    return {
        "dir_up": 1.0 if d == Dir.UP else 0.0,
        "setup_W3": 1.0 if setup == "W3" else 0.0,
        "setup_W5": 1.0 if setup == "W5" else 0.0,
        "setup_C": 1.0 if setup == "C" else 0.0,
        "atr_pct": atr_pct,
        "ema_fast_slow_pct": ema_fast_slow_pct,
        "price_above_ema_fast": price_above_ema_fast,
        "zone_width_pct": zone_width_pct,
        "dist_to_zone_center_pct": dist_to_zone_center_pct,
        "rsi": rsi if not np.isnan(rsi) else 50.0,
        "hour_sin": hour_sin, "hour_cos": hour_cos,
        "dow_sin": dow_sin, "dow_cos": dow_cos
    }

# --------------------------------------------------------------------------------------
# Backtester (inkl. ML mit Mindest-Pass-Rate)
# --------------------------------------------------------------------------------------
class Backtester:
    def __init__(self, daily:pd.DataFrame, h1:pd.DataFrame, m30:pd.DataFrame):
        self.daily = daily
        self.h1 = h1
        self.m30 = m30
        self.primary_engine = ElliottEngine(CFG["PRIMARY_ZZ_PCT"], CFG["PRIMARY_ZZ_ATR_MULT"], CFG["PRIMARY_MIN_IMP_ATR"])
        self.h1_engine = ElliottEngine(CFG["H1_ZZ_PCT"], CFG["H1_ZZ_ATR_MULT"], CFG["H1_MIN_IMP_ATR"])
        self.prim_imp: List[Impulse] = []
        self.prim_abc: List[ABC] = []
        self.impulses: List[Impulse] = []
        self.abcs: List[ABC] = []
        self.setups: List[Setup] = []
        self.sim_trades: List[SimTrade] = []
        self.trades: List[Trade] = []
        self.equity: List[Dict] = []
        self.model = None
        self.threshold = 0.5
        self.telemetry = dict(setups=0, filtered_daily=0, filtered_ema=0, filtered_vol=0, filtered_volatility=0, filtered_regime=0, no_touch=0, no_confirm=0, accepted=0)

    # ---------- Struktur ----------
    def analyze_structure(self):
        piv_d = self.primary_engine.zigzag(self.daily["close"].values, self.daily["ATR"].values)
        self.prim_imp = self.primary_engine.detect_impulses(piv_d, self.daily["close"].values, self.daily["ATR"].values)
        self.prim_abc = self.primary_engine.detect_abcs(piv_d)
        piv_h = self.h1_engine.zigzag(self.h1["close"].values, self.h1["ATR"].values)
        self.impulses = self.h1_engine.detect_impulses(piv_h, self.h1["close"].values, self.h1["ATR"].values)
        self.abcs     = self.h1_engine.detect_abcs(piv_h)

    def _preferred_tf(self, start_time:pd.Timestamp)->str:
        if not self.m30.empty and self.m30["date"].iloc[0] <= start_time <= self.m30["date"].iloc[-1]:
            return "30m"
        return "1h"

    def build_setups(self):
        self.setups.clear()
        for imp in self.impulses:
            p0,p1,p2,p3,p4,p5 = imp.points
            # Symmetrische Zonen/TPs wie im Original
            z3 = self.h1_engine.fib_zone(p0.price,p1.price,imp.direction,CFG["ENTRY_ZONE_W3"])
            t3 = self.h1.iloc[p2.idx+1]["date"]; tf3=self._preferred_tf(t3)
            tp1_3=self.h1_engine.fib_ext(p0.price,p1.price,imp.direction,CFG["TP1"])
            tp2_3=self.h1_engine.fib_ext(p0.price,p1.price,imp.direction,CFG["TP2"])
            self.setups.append(Setup("W3", imp.direction, t3, tf3, z3, p0.price, tp1_3, tp2_3, dict(src="impulse")))
            if CFG["USE_W5"]:
                z5=self.h1_engine.fib_zone(p2.price,p3.price,imp.direction,CFG["ENTRY_ZONE_W5"])
                t5=self.h1.iloc[p4.idx+1]["date"]; tf5=self._preferred_tf(t5)
                tp1_5=self.h1_engine.fib_ext(p2.price,p3.price,imp.direction,CFG["TP1"])
                tp2_5=self.h1_engine.fib_ext(p2.price,p3.price,imp.direction,CFG["TP2"])
                self.setups.append(Setup("W5", imp.direction, t5, tf5, z5, p2.price, tp1_5, tp2_5, dict(src="impulse")))
        for abc in self.abcs:
            a0,a1,b1,c1 = abc.points
            zc=self.h1_engine.fib_zone(a0.price,a1.price,abc.direction,CFG["ENTRY_ZONE_C"])
            tc=self.h1.iloc[b1.idx+1]["date"]; tfc=self._preferred_tf(tc)
            tp1_c=self.h1_engine.fib_ext(a0.price,a1.price,abc.direction,CFG["TP1"])
            tp2_c=self.h1_engine.fib_ext(a0.price,a1.price,abc.direction,CFG["TP2"])
            self.setups.append(Setup("C", abc.direction, tc, tfc, zc, b1.price, tp1_c, tp2_c, dict(src="abc")))
        self.setups.sort(key=lambda s:s.start_time)
        self.telemetry["setups"]=len(self.setups)

    # ---------- Simulation ----------
    def simulate_all(self):
        self.sim_trades.clear()
        for sp in self.setups:
            # Regime-Filter (ADX) als erstes Gate
            if CFG.get("USE_ADX", True):
                try:
                    didx=self.daily[self.daily["date"]<=pd.Timestamp(sp.start_time)].index
                    if len(didx)>0 and "ADX_14" in self.daily.columns:
                        cur_adx=float(self.daily.loc[didx.max(), "ADX_14"])
                        if not np.isnan(cur_adx) and cur_adx < CFG.get("ADX_TREND_THRESHOLD",25):
                            self.telemetry["filtered_regime"] = self.telemetry.get("filtered_regime",0)+1
                            continue
                except Exception:
                    pass
            df = df_for_tf(self.h1, self.m30, sp.entry_tf)
            if df.empty: continue
            start_i = idx_from_time(df, sp.start_time)
            if start_i is None: self.telemetry["no_touch"]+=1; continue
            if not ema_trend_ok(df.loc[start_i], sp.direction):
                self.telemetry["filtered_ema"]+=1; continue
            if not vol_ok(df.loc[start_i]):
                self.telemetry["filtered_vol"]+=1; continue

            win = CFG["ENTRY_WINDOW_M30"] if sp.entry_tf=="30m" else CFG["ENTRY_WINDOW_H1"]
            t_idx = first_touch(df, sp.start_time, sp.zone, win)
            if t_idx is None: self.telemetry["no_touch"]+=1; continue
            bars = CFG["CONFIRM_BARS_M30"] if sp.entry_tf=="30m" else CFG["CONFIRM_BARS_H1"]
            e_idx = confirm_idx(df, t_idx, sp.direction, bars, CFG["ALLOW_TOUCH_IF_NO_CONFIRM"])
            if e_idx is None: self.telemetry["no_confirm"]+=1; continue

            atr=float(df.iloc[e_idx]["ATR"])
            atr_mult = CFG["ATR_MULT_BUFFER"]
            buffer=atr_mult*atr
            stop = sp.stop_ref - buffer if sp.direction==Dir.UP else sp.stop_ref + buffer
            entry=float(df.iloc[e_idx]["close"])
            rps=abs(entry-stop)
            if rps<=1e-9: continue

            max_hold=CFG["MAX_HOLD_M30"] if sp.entry_tf=="30m" else CFG["MAX_HOLD_H1"]
            x_idx,x_price,ps,mae,mfe = simulate(df, e_idx, entry, sp.direction, stop, sp.tp1, sp.tp2, max_hold)
            feats = build_features(df, e_idx, sp.direction, sp.setup, sp.zone)
            label = 1 if ps>0 else 0

            self.sim_trades.append(SimTrade(sp.entry_tf, e_idx, x_idx, entry, x_price, ps, rps,
                                            sp.setup, "LONG" if sp.direction==Dir.UP else "SHORT",
                                            df.iloc[e_idx]["date"], df.iloc[x_idx]["date"],
                                            stop, sp.tp1, sp.tp2, mae, mfe, feats, label))
            self.telemetry["accepted"]+=1

    # ---------- ML ----------
    def _XY(self, trades:List[SimTrade])->Tuple[pd.DataFrame,np.ndarray]:
        X=pd.DataFrame([t.features for t in trades])
        for c in FEATURE_COLUMNS:
            if c not in X.columns: X[c]=0.0
        return X[FEATURE_COLUMNS], np.array([t.label for t in trades], dtype=int)

    def _make_calibrator(self, estimator, method, cv):
        # Nicht genutzt in der Original-Baseline
        return estimator

    def train_model(self, train_trades:List[SimTrade]):
        X,y=self._XY(train_trades)
        clf=GradientBoostingClassifier(random_state=42).fit(X,y)
        self.model=clf
        self.threshold=0.5
        # Optionale Diagnose
        try:
            probs=clf.predict_proba(X)[:,1]
            self.ml_train_pass_rate = float((probs>=self.threshold).mean())
        except Exception:
            self.ml_train_pass_rate = None

    def build_equity(self, train_until:pd.Timestamp):
        self.trades.clear(); self.equity.clear()
        cap=CFG["START_CAPITAL"]; eq_map:Dict[pd.Timestamp,float]={}

        # Test-Passrate prüfen/relaxen
        oos=[t for t in self.sim_trades if t.time_in>train_until]
        if self.model is not None and oos:
            Xo,_=self._XY(oos); probs=self.model.predict_proba(Xo)[:,1]
            raw_rate=float((probs>=self.threshold).mean())
            self.ml_test_pass_rate_raw=raw_rate
            if raw_rate < CFG["ML_MIN_PASS_RATE_TEST"]:
                thr_relaxed=float(np.quantile(probs, 1-CFG["ML_MIN_PASS_RATE_TEST"]))
                self.threshold=min(self.threshold, thr_relaxed)

        # --- Dynamische Risiko Hilfsfunktionen ---
        def _dd_percent(current_cap:float, highest_cap:float)->float:
            return (current_cap/highest_cap - 1.0)*100.0 if highest_cap>0 else 0.0
        def _risk_multiplier_for_dd(cur_dd:float)->float:
            if not CFG.get("DYNAMIC_DD_RISK", False):
                return 1.0
            steps=CFG.get("DD_RISK_STEPS", [])
            mult=1.0
            for thr,m in sorted(steps, key=lambda x:x[0]):  # thr ist negativ (z.B. -10)
                if cur_dd <= thr:
                    mult=m
            return mult
        trade_returns=[]  # für Vol-Zielsteuerung
        def _vol_adjustment()->float:
            if not CFG.get("USE_VOL_TARGET", False):
                return 1.0
            target=CFG.get("TARGET_ANNUAL_VOL", 0.25)
            window=CFG.get("VOL_WINDOW_TRADES", 40)
            if len(trade_returns)<5:
                return 1.0
            recent=trade_returns[-window:]
            # Approx annual vol: std(per-trade R) * sqrt(trades_per_year). Für Proxy nehmen wir std und normalisieren Richtung Ziel.
            s=np.std(recent, ddof=1)
            if s<=1e-9:
                return 1.0
            # Ziel: grob s -> target/ sqrt(annual_trades_factor). Vereinfachung: scale = target_ref / s
            # Da wir R-Multiples haben: angenommene annual trades ~ len(self.trades)/years später -> hier simpler scaler clampen.
            scale=target/ (s*4)  # heuristisch (4 ~ sqrt(approx trades/year Anteil))
            return max(0.4, min(1.6, scale))

        max_stop_dd=CFG.get("MAX_DRAWDOWN_STOP", -1e9)
        highest_global=cap

        def add(sim:SimTrade, prob:Optional[float]):
            nonlocal cap
            nonlocal highest_global
            if CFG.get("MAX_DRAWDOWN_STOP", -1e9) > -1e8:  # wurde gesetzt
                # Prüfe aktuellen Drawdown (gegen highest_global)
                cur_dd=_dd_percent(cap, highest_global)
                if cur_dd <= max_stop_dd:
                    return  # Trade verweigern – Hard Stop
            # Basis-Risiko
            base_risk=CFG["RISK_PER_TRADE"]
            # Drawdown Multiplikator
            cur_dd=_dd_percent(cap, highest_global)
            dd_mult=_risk_multiplier_for_dd(cur_dd)
            # Vol-Ziel Multiplikator
            vol_mult=_vol_adjustment()
            eff_risk=base_risk*dd_mult*vol_mult
            eff_risk=max(CFG.get("RISK_PER_TRADE_MIN", eff_risk), min(eff_risk, CFG.get("RISK_PER_TRADE_MAX", eff_risk)))
            size=(eff_risk*cap)/max(sim.risk_per_share,1e-9)
            if sim.direction=="SHORT": size *= CFG["SIZE_SHORT_FACTOR"]
            if prob is not None and CFG["SIZE_BY_PROB"]:
                frac=max(0.0,(prob-self.threshold)/max(1e-6,1-self.threshold))
                scale=CFG["PROB_SIZE_MIN"] + (CFG["PROB_SIZE_MAX"]-CFG["PROB_SIZE_MIN"])*frac
                size*=scale
            size=int(max(1,size))
            pnl = (sim.per_share * size)
            cap+=pnl
            # Speichere R-Multiple für Vol-Steuerung
            trade_returns.append(sim.per_share/max(sim.risk_per_share,1e-9))
            # Exit auf nächste 1H-Zeit mappen
            h1_after=self.h1[self.h1["date"]>=sim.time_out]
            map_time=h1_after["date"].iloc[0] if len(h1_after) else self.h1["date"].iloc[-1]
            eq_map[map_time]=cap
            rr=sim.per_share/max(sim.risk_per_share,1e-9)
            self.trades.append(Trade(sim.entry_tf,sim.entry_idx,sim.exit_idx,sim.entry,sim.exit,pnl,size,rr,
                                     sim.setup,sim.direction,sim.time_in,sim.time_out,sim.stop,sim.tp1,sim.tp2,sim.mae_r,sim.mfe_r,
                                     prob=prob, risk_per_share=sim.risk_per_share))
            highest_global=max(highest_global, cap)

        pre_ml=len([t for t in self.sim_trades if t.time_in>train_until]); post_ml=0
        for sim in self.sim_trades:
            if sim.time_in<=train_until:
                add(sim, None)
            else:
                if self.model is None:
                    add(sim, None)
                else:
                    X=pd.DataFrame([sim.features])[FEATURE_COLUMNS]
                    p=float(self.model.predict_proba(X)[0,1])
                    if p>=self.threshold:
                        add(sim, p); post_ml+=1
        self.ml_test_pass_rate = (post_ml/max(1,pre_ml)) if pre_ml>0 else None

        highest=CFG["START_CAPITAL"]; cur=CFG["START_CAPITAL"]
        for ts in self.h1["date"]:
            if ts in eq_map: cur=eq_map[ts]
            highest=max(highest, cur)
            dd=(cur - highest)/max(highest,1e-9)*100
            self.equity.append(dict(date=ts, capital=cur, dd=dd))

    def run(self)->Dict:
        self.analyze_structure()
        self.build_setups()
        self.simulate_all()
        if not self.sim_trades: return {}

        times=sorted([t.time_in for t in self.sim_trades])
        split_idx=max(1, int(len(times)*CFG["TRAIN_FRAC"]))
        train_until=times[split_idx-1]

        if CFG["USE_ML"]:
            train=[t for t in self.sim_trades if t.time_in<=train_until]
            if len(train)>=20:
                self.train_model(train)
                # Threshold Optimization (Validation = OOS until now)
                if CFG.get("OPTIMIZE_ML_THRESHOLD", False) and self.model is not None:
                    try:
                        val=[t for t in self.sim_trades if t.time_in>train_until]
                        if len(val)>=25:
                            Xv,_=self._XY(val); probs=self.model.predict_proba(Xv)[:,1]
                            labels=np.array([t.label for t in val])
                            # Kandidaten-Thresholds (Quantile Raster)
                            qs=np.linspace(0.2,0.9,15)
                            best_thr=self.threshold; best_score=-1e9
                            for q in qs:
                                thr=np.quantile(probs,q)
                                mask=probs>=thr
                                if mask.sum()<5: continue
                                sel=labels[mask]
                                win_rate=sel.mean() if len(sel)>0 else 0
                                # Approx. Gewinn je Trade = win_rate - (1-win_rate)*(avg_loss_ratio) -> hier vereinfachen: score = win_rate - 0.5*(1-win_rate)
                                score=win_rate - 0.5*(1-win_rate)
                                if score>best_score:
                                    best_score=score; best_thr=thr
                            self.threshold=float(best_thr)
                    except Exception:
                        pass
            else:
                self.model=None; self.threshold=0.5; self.ml_train_pass_rate=None
        else:
            self.model=None; self.threshold=0.5; self.ml_train_pass_rate=None

        self.build_equity(train_until)
        metrics=self.metrics()
        print("\n--- Telemetrie ---")
        print(f"Setups gesamt: {self.telemetry['setups']} | akzeptiert bis Entry: {self.telemetry['accepted']}")
        print(f"Filter: daily={self.telemetry.get('filtered_daily',0)}, regime(ADX)={self.telemetry.get('filtered_regime',0)}, ema={self.telemetry['filtered_ema']}, vol={self.telemetry['filtered_vol']}, no_touch={self.telemetry['no_touch']}, no_confirm={self.telemetry['no_confirm']}")
        if CFG["USE_ML"]:
            print(f"ML threshold: {self.threshold:.3f} | Train pass-rate: {self.ml_train_pass_rate} | Test pass-rate used: {self.ml_test_pass_rate}")
        return metrics

    # ---------- Metrics ----------
    def metrics(self)->Dict:
        if not self.equity: return {}
        pnl=[t.pnl for t in self.trades]
        wins=[x for x in pnl if x>0]; losses=[x for x in pnl if x<=0]
        start=CFG["START_CAPITAL"]; end=self.equity[-1]["capital"]
        total_return=(end-start)/start*100 if start>0 else 0.0

        # Periodische Renditen (dezimal) aus 1H Equity (ggf. leere Schritte = 0)
        eq=pd.DataFrame(self.equity)
        eq["date"]=pd.to_datetime(eq["date"])
        eq["ret"]=eq["capital"].pct_change().fillna(0.0)  # dezimal
        rets=eq["ret"].values

        # Perioden pro Jahr dynamisch (robust bei Lücken)
        span_years=max((eq["date"].iloc[-1]-eq["date"].iloc[0]).days/365.0, 1e-6)
        periods_per_year = len(rets)/span_years if span_years>0 else 0.0

        mu = float(np.mean(rets)) if len(rets) else 0.0
        sigma = float(np.std(rets, ddof=1)) if len(rets)>1 else 0.0
        rf_ann = RISK_FREE_RATE/100.0
        rf_per_period = (1.0 + rf_ann)**(1.0/max(periods_per_year,1e-6)) - 1.0 if periods_per_year>0 else 0.0

        vol_annual = sigma*math.sqrt(max(periods_per_year,1e-6))
        vol_pct = vol_annual*100.0

        sharpe = ((mu - rf_per_period)/sigma)*math.sqrt(periods_per_year) if sigma>1e-12 and periods_per_year>0 else 0.0

        downside_arr = np.minimum(rets - rf_per_period, 0.0)
        down_sigma = float(np.std(downside_arr, ddof=1)) if len(downside_arr)>1 and np.any(downside_arr<0) else 0.0
        sortino = ((mu - rf_per_period)/down_sigma)*math.sqrt(periods_per_year) if down_sigma>1e-12 and periods_per_year>0 else 0.0

        # CAGR über Kapitalverlauf (robust)
        years = max((pd.Timestamp(self.equity[-1]["date"]) - pd.Timestamp(self.equity[0]["date"])).days / 365.0, 1e-6)
        try:
            cagr = ((end/start)**(1/years)-1)*100 if start>0 else 0.0
            if not np.isfinite(cagr) or cagr > 1e6 or cagr < -1e6:
                cagr = 0.0
        except (OverflowError, ZeroDivisionError, ValueError):
            cagr = 0.0

        # Drawdown-Kennzahlen
        max_dd=min(e["dd"] for e in self.equity) if self.equity else 0.0  # in %
        dd_dec=np.array([-min(0.0, e["dd"]/100.0) for e in self.equity], dtype=float)  # positive Tiefen
        ulcer_index=math.sqrt(float(np.mean(dd_dec**2))) if len(dd_dec)>0 else 0.0
        upi=((cagr/100.0)-rf_ann)/ulcer_index if ulcer_index>1e-12 else 0.0

        # Gain-to-Pain auf Periodenrenditen
        pos_sum=float(np.sum(rets[rets>0])) if np.any(rets>0) else 0.0
        neg_sum=float(np.sum(rets[rets<0])) if np.any(rets<0) else 0.0
        gain_to_pain = (pos_sum/abs(neg_sum)) if neg_sum!=0 else np.inf

        # Exposure (vereinfachte Approx: Summe Haltedauer / Gesamtdauer)
        total_hours = (eq["date"].iloc[-1]-eq["date"].iloc[0]).total_seconds()/3600.0
        held_hours = float(np.sum([(t.time_out - t.time_in).total_seconds()/3600.0 for t in self.trades]))
        exposure = min(1.0, held_hours/max(total_hours,1e-6)) if total_hours>0 else 0.0

        # Sonstiges
        hit=len(wins)/len(pnl)*100 if pnl else 0.0
        avg_win=float(np.mean(wins)) if wins else 0.0
        avg_loss=float(np.mean(losses)) if losses else 0.0
        payoff=abs(avg_win)/abs(avg_loss) if avg_loss!=0 else np.nan
        profit_factor=(sum(wins)/abs(sum(losses))) if losses else np.inf
        expectancy=(hit/100.0)*avg_win + (1-hit/100.0)*avg_loss

        by_type:Dict[str,List[float]]={}; by_dir={"LONG":[], "SHORT":[]}
        for t in self.trades:
            by_type.setdefault(t.setup,[]).append(t.pnl)
            by_dir[t.direction].append(t.pnl)
        type_stats={k:dict(count=len(v),sum=float(np.sum(v)),avg=float(np.mean(v)) if v else 0.0) for k,v in by_type.items()}
        dir_stats={k:dict(count=len(v),sum=float(np.sum(v)),avg=float(np.mean(v)) if v else 0.0) for k,v in by_dir.items()}
        durations=[(t.time_out - t.time_in).total_seconds()/3600.0 for t in self.trades]
        mae=[t.mae_r for t in self.trades]; mfe=[t.mfe_r for t in self.trades]

        # Erweiterte Fehler-/Chance Kennzahlen
        long_pnls=by_dir.get("LONG",[]); short_pnls=by_dir.get("SHORT",[])
        long_wins=[x for x in long_pnls if x>0]; long_losses=[x for x in long_pnls if x<=0]
        short_wins=[x for x in short_pnls if x>0]; short_losses=[x for x in short_pnls if x<=0]
        winrate_long=len(long_wins)/len(long_pnls)*100 if long_pnls else 0.0
        winrate_short=len(short_wins)/len(short_pnls)*100 if short_pnls else 0.0
        pf_long=(sum(long_wins)/abs(sum(long_losses))) if long_losses else (np.inf if long_wins else 0.0)
        pf_short=(sum(short_wins)/abs(sum(short_losses))) if short_losses else (np.inf if short_wins else 0.0)

        # Expectancy in R (Durchschnitts R-Multiple)
        R_list=[t.rr for t in self.trades]
        expectancy_R=float(np.mean(R_list)) if R_list else 0.0

        # Kelly (vereinfachte Variante basierend auf R-Avg Gew/Verl)
        avg_R_win=float(np.mean([r for r,p in zip(R_list,pnl) if p>0])) if any(p>0 for p in pnl) else 0.0
        avg_R_loss=abs(float(np.mean([r for r,p in zip(R_list,pnl) if p<=0]))) if any(p<=0 for p in pnl) else 0.0
        p_win=len(wins)/len(pnl) if pnl else 0.0
        kelly = (p_win - (1-p_win)/max(avg_R_win/avg_R_loss,1e-9)) if avg_R_loss>0 and avg_R_win>0 else 0.0
        if not np.isfinite(kelly): kelly=0.0
        kelly_pct=kelly*100.0

        avg_mae_r=float(np.mean(mae)) if mae else 0.0
        avg_mfe_r=float(np.mean(mfe)) if mfe else 0.0
        median_mae_r=float(np.median(mae)) if mae else 0.0
        median_mfe_r=float(np.median(mfe)) if mfe else 0.0
        best_trade=float(max(pnl)) if pnl else 0.0
        worst_trade=float(min(pnl)) if pnl else 0.0
        avg_size=float(np.mean([t.size for t in self.trades])) if self.trades else 0.0
        pnl_std=float(np.std(pnl, ddof=1)) if len(pnl)>1 else 0.0
        downside_deviation=float(np.std([x for x in pnl if x<0], ddof=1)) if len([x for x in pnl if x<0])>1 else 0.0
        equity_curve_len=len(self.equity)

        # Streaks
        signs=[1 if x>0 else -1 for x in pnl]
        streaks=[]; cur=0; prev=None
        for s in signs:
            if prev is None or s==prev: cur+=1
            else: streaks.append(prev*cur); cur=1
            prev=s
        if prev is not None: streaks.append(prev*cur)
        max_win_streak=max([x for x in streaks if x>0], default=0)
        max_loss_streak=max([abs(x) for x in streaks if x<0], default=0)

        # Monthly (wie gehabt) + Heatmap
        eq["month"]=eq["date"].dt.to_period("M")
        monthly=(eq.groupby("month")["ret"].apply(lambda s:(1+s).prod()-1)).reset_index()
        monthly["ret_pct"]=monthly["ret"]*100.0
        monthly["year"]=monthly["month"].dt.year
        monthly["m"]=monthly["month"].dt.month
        heatmap = monthly.pivot_table(index="year", columns="m", values="ret_pct", aggfunc="first").sort_index()

        # Trades/Jahr
        trades_per_year = len(self.trades)/years if years>0 else 0.0

        out=dict(
            total_return=total_return,cagr=cagr,trades=len(self.trades),hit=hit,avg_win=avg_win,avg_loss=avg_loss,
            payoff=payoff,profit_factor=profit_factor,expectancy=expectancy,
            vol=vol_pct,sharpe=sharpe,sortino=sortino,max_dd=max_dd,calmar=(cagr/abs(max_dd) if max_dd<0 else 0.0),
            pnl=pnl,returns_r=[t.rr for t in self.trades],equity=self.equity,trades_list=self.trades,
            type_stats=type_stats,dir_stats=dir_stats,durations=durations,mae=mae,mfe=mfe,monthly=monthly,
            periods_per_year=periods_per_year, rf_per_period=rf_per_period, ulcer_index=ulcer_index, upi=upi,
            gain_to_pain=gain_to_pain, trades_per_year=trades_per_year, exposure=exposure,
            max_win_streak=max_win_streak, max_loss_streak=max_loss_streak, avg_R=float(np.mean([t.rr for t in self.trades])) if self.trades else 0.0,
            median_hold_hours=float(np.median(durations)) if durations else 0.0, avg_hold_hours=float(np.mean(durations)) if durations else 0.0,
            heatmap=heatmap
        )

        # Zusätzliche Metriken anreichern
        out.update(dict(
            winrate_long=winrate_long, winrate_short=winrate_short,
            pf_long=pf_long, pf_short=pf_short,
            expectancy_R=expectancy_R,
            avg_R_win=avg_R_win, avg_R_loss=avg_R_loss,
            kelly_pct=kelly_pct,
            avg_mae_r=avg_mae_r, avg_mfe_r=avg_mfe_r,
            median_mae_r=median_mae_r, median_mfe_r=median_mfe_r,
            best_trade=best_trade, worst_trade=worst_trade,
            avg_size=avg_size, pnl_std=pnl_std, downside_deviation=downside_deviation,
            equity_curve_len=equity_curve_len
        ))

        # ML‑Diagnostik
        if self.model is not None and self.sim_trades:
            times=sorted([t.time_in for t in self.sim_trades]); split_idx=max(1,int(len(times)*CFG["TRAIN_FRAC"])); split_time=times[split_idx-1]
            te=[t for t in self.sim_trades if t.time_in>split_time]
            if len(te)>=5:
                Xte,_=self._XY(te); yte=np.array([t.label for t in te],dtype=int)
                prob_te=self.model.predict_proba(Xte)[:,1]
                fpr,tpr,_=roc_curve(yte,prob_te); rc,pr,_=precision_recall_curve(yte,prob_te)
                out["ml_auc"]=auc(fpr,tpr); out["ml_ap"]=average_precision_score(yte,prob_te)
                pt,pp=calibration_curve(yte,prob_te, n_bins=min(10,len(yte)))
                out["ml_calib"]=(pt,pp); out["ml_roc"]=(fpr,tpr); out["ml_pr"]=(rc,pr)
                try:
                    pi=permutation_importance(self.model,Xte,yte,n_repeats=10,random_state=42)
                    out["ml_perm_importance"]=(list(Xte.columns), list(pi.importances_mean))
                except Exception:
                    pass
                out["ml_threshold"]=self.threshold
        return out

# --------------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------------
def plot_report(daily:pd.DataFrame, h1:pd.DataFrame, bt:Backtester, metrics:Dict, pdf_path:str):

    with PdfPages(pdf_path) as pdf:
        # Seite 1: Equity & Drawdown (verbesserte Skalierung)
        fig, axes = plt.subplots(2, 1, figsize=(14, 9), constrained_layout=True)
        eq = metrics["equity"]
        dates = [pd.Timestamp(e["date"]) for e in eq]
        caps = [e["capital"] for e in eq]
        dds = [e["dd"] for e in eq]
        # Equity Curve
        axes[0].plot(dates, caps, color="#FF5252", lw=1.6, label=f'Final: ${int(caps[-1]):,}')
        axes[0].axhline(CFG["START_CAPITAL"], color="gray", ls="--", label="Initial")
        axes[0].legend()
        axes[0].grid(True, alpha=.3)
        axes[0].set_title("Equity Curve")
        # Verbesserte Y-Skalierung & optional log
        y_min, y_max = float(min(caps)), float(max(caps))
        y_range = max(1.0, y_max - y_min)
        margin = 0.04 * y_range
        axes[0].set_ylim(y_min - margin, y_max + margin)
        ratio = (y_max - y_min) / max(y_min, 1.0)
        if ratio > CFG.get("EQUITY_LOG_THRESHOLD", 5.0):
            axes[0].set_yscale('log')
        # Kompaktere Zahlenformatierung
        import matplotlib.ticker as mticker
        def _human(v):
            for unit in ['', 'K', 'M', 'B']:
                if abs(v) < 1000: return f"{v:,.0f}{unit}".replace(',','.')
                v /= 1000.0
            return f"{v:,.0f}T".replace(',','.')
        axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda _x,_p:_human(_x)))
        # Drawdown
        axes[1].fill_between(dates, dds, 0, color="#FF9999", alpha=.7)
        axes[1].plot(dates, dds, color="#B71C1C", lw=1.0)
        axes[1].set_title("Drawdown")
        axes[1].grid(True, alpha=.3)
        # Improved y-scaling for drawdown
        dd_min, dd_max = min(dds), max(dds)
        axes[1].set_ylim(dd_min - 0.05 * abs(dd_min), 5)
        # X-axis formatting
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
        pdf.savefig(fig)
        plt.close(fig)

        # Seite 2: Ausführliche Kennzahlen-Tabelle (mit neuen KPIs)
        import matplotlib.table as tbl
        from scipy.stats import skew, kurtosis
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.axis('off')
        # Calculate additional KPIs
        pnl = metrics.get('pnl', [])
        returns = metrics.get('returns_r', [])
        skewness = skew(pnl) if len(pnl) > 2 else float('nan')
        kurt = kurtosis(pnl) if len(pnl) > 2 else float('nan')
        ulcer = metrics.get('ulcer_index', float('nan'))
        payoff = metrics.get('payoff', float('nan'))
        avg_win = metrics.get('avg_win', float('nan'))
        avg_loss = metrics.get('avg_loss', float('nan'))
        # Add more KPIs as needed
        stats = [
            ["Total Return", f"{metrics['total_return']:.2f}%"],
            ["CAGR", f"{metrics['cagr']:.2f}%"],
            ["Winrate", f"{metrics['hit']:.2f}%"],
            ["Profit Factor", f"{metrics['profit_factor']:.2f}"],
            ["Expectancy", f"${metrics['expectancy']:.2f}"],
            ["Sharpe Ratio", f"{metrics['sharpe']:.2f}"],
            ["Sortino Ratio", f"{metrics['sortino']:.2f}"],
            ["UPI (Ulcer Perf. Index)", f"{metrics['upi']:.2f}"],
            ["Ulcer Index", f"{ulcer:.2f}"],
            ["Gain-to-Pain", f"{metrics['gain_to_pain']:.2f}"],
            ["Max Drawdown", f"{metrics['max_dd']:.2f}%"],
            ["Calmar Ratio", f"{metrics['calmar']:.2f}"],
            ["Volatility (ann.)", f"{metrics['vol']:.2f}%"],
            ["Skewness (P&L)", f"{skewness:.2f}"],
            ["Kurtosis (P&L)", f"{kurt:.2f}"],
            ["Payoff Ratio", f"{payoff:.2f}"],
            ["Avg. Win", f"${avg_win:.2f}"],
            ["Avg. Loss", f"${avg_loss:.2f}"],
            ["Trades", f"{metrics['trades']}"],
            ["Avg. Trade Duration (h)", f"{metrics['avg_hold_hours']:.2f}"],
            ["Median Trade Duration (h)", f"{metrics['median_hold_hours']:.2f}"],
            ["Avg. R-Multiple", f"{metrics['avg_R']:.2f}"],
            ["Exposure", f"{metrics['exposure']:.2%}"],
            ["Trades/Jahr", f"{metrics['trades_per_year']:.2f}"],
            ["Max Win Streak", f"{metrics['max_win_streak']}"],
            ["Max Loss Streak", f"{metrics['max_loss_streak']}"],
            ["Winrate Long", f"{metrics.get('winrate_long',0):.2f}%"],
            ["Winrate Short", f"{metrics.get('winrate_short',0):.2f}%"],
            ["PF Long", f"{metrics.get('pf_long',0):.2f}" if np.isfinite(metrics.get('pf_long',0)) else 'inf'],
            ["PF Short", f"{metrics.get('pf_short',0):.2f}" if np.isfinite(metrics.get('pf_short',0)) else 'inf'],
            ["Expectancy (R)", f"{metrics.get('expectancy_R',0):.2f}"],
            ["Avg R Win", f"{metrics.get('avg_R_win',0):.2f}"],
            ["Avg R Loss", f"{-metrics.get('avg_R_loss',0):.2f}"],
            ["Kelly %", f"{metrics.get('kelly_pct',0):.2f}%"],
            ["Avg MAE (R)", f"{metrics.get('avg_mae_r',0):.2f}"],
            ["Avg MFE (R)", f"{metrics.get('avg_mfe_r',0):.2f}"],
            ["Median MAE (R)", f"{metrics.get('median_mae_r',0):.2f}"],
            ["Median MFE (R)", f"{metrics.get('median_mfe_r',0):.2f}"],
            ["Best Trade $", f"{metrics.get('best_trade',0):.2f}"],
            ["Worst Trade $", f"{metrics.get('worst_trade',0):.2f}"],
            ["Avg Size", f"{metrics.get('avg_size',0):.1f}"],
            ["PnL Std", f"{metrics.get('pnl_std',0):.2f}"],
            ["Downside Dev", f"{metrics.get('downside_deviation',0):.2f}"],
            ["Equity Points", f"{metrics.get('equity_curve_len',0)}"],
        ]
        table = tbl.Table(ax, bbox=[0, 0, 1, 1])
        for i, (k, v) in enumerate(stats):
            table.add_cell(i, 0, 0.4, 0.04, text=k, loc='left', facecolor='#f5f5f5')
            table.add_cell(i, 1, 0.6, 0.04, text=v, loc='left')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        ax.add_table(table)
        ax.set_title("Kennzahlen (ausführlich, erweitert)", fontsize=16)
        pdf.savefig(fig)
        plt.close(fig)

        # ...bestehende Plots (Distribution, Monthly, Setup/Direction, Duration, Streaks etc.) ...

        # Seite 4: ML‑Diagnostik
        if "ml_auc" in metrics:
            fig=plt.figure(figsize=(14,9),constrained_layout=True); gs=fig.add_gridspec(2,2)
            ax1=fig.add_subplot(gs[0,0]); ax2=fig.add_subplot(gs[0,1]); ax3=fig.add_subplot(gs[1,0]); ax4=fig.add_subplot(gs[1,1])
            fpr,tpr=metrics["ml_roc"]; ax1.plot(fpr,tpr,color="#1E88E5"); ax1.plot([0,1],[0,1],ls="--",color="#999"); ax1.set_title(f"ROC (AUC={metrics['ml_auc']:.3f})")
            rc,pr=metrics["ml_pr"]; ax2.plot(rc,pr,color="#43A047"); ax2.set_title(f"PR (AP={metrics['ml_ap']:.3f})")
            if "ml_calib" in metrics:
                pt,pp=metrics["ml_calib"]; ax3.plot(pp,pt,marker="o",color="#FB8C00"); ax3.plot([0,1],[0,1],ls="--",color="#999"); ax3.set_title("Calibration")
            if "ml_perm_importance" in metrics:
                names,imps=metrics["ml_perm_importance"]; order=np.argsort(imps)[::-1][:10]
                ax4.bar([names[i] for i in order],[imps[i] for i in order],color="#8E24AA"); ax4.set_title("Permutation Importance"); ax4.tick_params(axis='x',rotation=45)
            pdf.savefig(fig); plt.close(fig)

        # Seite 5: Struktur-Chart (gefilterte übergeordnete Wellen)
        fig,ax=plt.subplots(figsize=(18,9),constrained_layout=True)
        ax.plot(daily["date"], daily["close"], color="#1e88e5", lw=1.0, alpha=0.6, label="Price (Daily)")

        # Filter: Mindest-% Bewegung UND Mindestdauer
        min_pct = CFG.get("WAVE_MIN_PCT", 0.08)
        min_dur = CFG.get("WAVE_MIN_DURATION_DAYS", 40)
        def _wave_ok(points):
            if len(points)<2: return False
            i0, i1 = points[0].idx, points[-1].idx
            if i0>=len(daily) or i1>=len(daily): return False
            p0, p1 = daily.iloc[i0]["close"], daily.iloc[i1]["close"]
            if p0==0 or pd.isna(p0) or pd.isna(p1): return False
            move = abs(p1-p0)/p0
            dur = (daily.iloc[i1]["date"] - daily.iloc[i0]["date"]).days
            return move >= min_pct and dur >= min_dur

        prim_imp_filtered = [w for w in bt.prim_imp if _wave_ok(w.points)] if getattr(bt,'prim_imp',None) else []
        prim_abc_filtered = [w for w in bt.prim_abc if _wave_ok(w.points)] if getattr(bt,'prim_abc',None) else []

        # Plot-Funktion mit größeren Label-Abständen
        def _plot_degree(df, imps, abcs, color_imp, color_abc, lw, gap_days):
            label_gap = pd.Timedelta(days=CFG.get("WAVE_LABEL_GAP_DAYS", 60))
            last_label_time=None
            if imps:
                for imp in imps:
                    xs=[df.iloc[p.idx]["date"] for p in imp.points]; ys=[p.price for p in imp.points]
                    ax.plot(xs,ys,color=color_imp,lw=lw,alpha=0.95)
                    # Nur Start, Mitte (3), Ende labeln
                    key_indices=[0,2,len(imp.points)-1]
                    names=["1","3","(end)"]
                    for ki,name in zip(key_indices,names):
                        t=df.iloc[imp.points[ki].idx]["date"]; y=imp.points[ki].price
                        if (last_label_time is None) or (t-last_label_time)>=label_gap:
                            ax.text(t,y,name,fontsize=10,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec=color_imp,alpha=0.85),color=color_imp)
                            last_label_time=t
            if abcs:
                for pat in abcs:
                    xs=[df.iloc[p.idx]["date"] for p in pat.points]; ys=[p.price for p in pat.points]
                    ax.plot(xs,ys,color=color_abc,lw=lw,alpha=0.95,ls='--')
                    key_pts=[(0,'A'),(1,'B'),(-1,'C')]
                    for idx_name in key_pts:
                        idx,name=idx_name
                        real_idx = pat.points[idx].idx if idx>=0 else pat.points[idx].idx
                        t=df.iloc[real_idx]["date"]; y=pat.points[idx].price
                        if (last_label_time is None) or (t-last_label_time)>=label_gap:
                            ax.text(t,y,name,fontsize=10,bbox=dict(boxstyle="round,pad=0.2",fc="white",ec=color_abc,alpha=0.85),color=color_abc)
                            last_label_time=t

        _plot_degree(daily, prim_imp_filtered, prim_abc_filtered, "#8E24AA", "#FB8C00", 1.8, CFG.get("WAVE_LABEL_GAP_DAYS",60))

        ax.set_title("Elliott Structure – Primary (gefiltert)")
        ax.legend(loc="upper left"); ax.grid(True,alpha=.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m")); ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
        pdf.savefig(fig); plt.close(fig)

        # Seite 6: Monats-Heatmap
        hm=metrics["heatmap"]
        if hm is not None and hm.size>0:
            fig,ax=plt.subplots(figsize=(14,7),constrained_layout=True)
            months = [1,2,3,4,5,6,7,8,9,10,11,12]
            # Reindex, um alle Monate zu zeigen
            hm_plot = hm.reindex(columns=months)
            norm = TwoSlopeNorm(vmin=min(-20, np.nanmin(hm_plot.values) if np.isfinite(np.nanmin(hm_plot.values)) else -10),
                                vcenter=0, vmax=max(20, np.nanmax(hm_plot.values) if np.isfinite(np.nanmax(hm_plot.values)) else 10))
            im=ax.imshow(hm_plot.values, aspect="auto", cmap="RdYlGn", norm=norm)
            # Ticks
            ax.set_yticks(range(len(hm_plot.index))); ax.set_yticklabels(hm_plot.index)
            ax.set_xticks(range(12)); ax.set_xticklabels(["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"], rotation=0)
            ax.set_title("Monatsrenditen Heatmap (%)")
            # Zahlen annotieren
            for i in range(hm_plot.shape[0]):
                for j in range(hm_plot.shape[1]):
                    val = hm_plot.values[i,j]
                    if np.isfinite(val):
                        ax.text(j,i,f"{val:+.1f}", ha="center", va="center", color="black", fontsize=9)
            cbar=fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label("%")
            pdf.savefig(fig); plt.close(fig)

    print(f"Report gespeichert: {pdf_path}")

# --------------------------------------------------------------------------------------
# Main + CLI
# --------------------------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Elliott Perfect System 5 – Multi‑TF Backtest mit ML‑Filter",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Beispiele:\n"
            "  1) Standard Nasdaq QQQ (aggressiv)\n"
            "     python Ur-EW-Code.py\n\n"
            "  2) Balanced Profil auf SPY ohne ML\n"
            "     python Ur-EW-Code.py -p balanced -s SPY --no-ml\n\n"
            "  3) EURUSD mit historischer CSV Nutzung (falls vorhanden)\n"
            "     python Ur-EW-Code.py -s EURUSD=X --csv\n\n"
            "  4) Intermediate Struktur mit einblenden\n"
            "     python Ur-EW-Code.py -s QQQ --show-intermediate\n\n"
            "  5) Gebühren & Slippage berücksichtigen (0.1% Fee, 0.05% Slippage)\n"
            "     python Ur-EW-Code.py -s QQQ --fee 0.001 --slippage 0.0005\n\n"
            "  6) Langsamer Order Fill (z.B. Latenz Simulation 5s)\n"
            "     python Ur-EW-Code.py --slow 5\n\n"
            "  7) Monatliche Auszahlung von 5.000$ (Cash-Out)\n"
            "     python Ur-EW-Code.py --monthly-payout 5000\n\n"
            "  8) Nur CSV Daten laden (statt yfinance)\n"
            "     python Ur-EW-Code.py --csv -s QQQ\n\n"
            "  9) Report für Gold Futures (GC=F)\n"
            "     python Ur-EW-Code.py -s GC=F\n\n"
            " 10) Minimale Ausgabe + Balanced Profil + eigenes Symbol\n"
            "     python Ur-EW-Code.py -p balanced -s ^GSPC --no-ml\n\n"
            "Hinweis: ML Pass-Rate Guards passen Threshold dynamisch an.\n"
            "         CSV-Dateinamen siehe Code (load_data).\n"
        )
    )
    p.add_argument("--symbol", "-s", default=os.getenv("EW_SYMBOL", "QQQ"),
                   help="yfinance Ticker (z.B. QQQ, ^NDX, ^IXIC, SPY, ES=F). Default: QQQ")
    p.add_argument("--profile", "-p", choices=["balanced","aggressive","adaptive"], default=os.getenv("EW_PROFILE", PROFILE),
                   help="Profil mit Parametern. Default: aggressive")
    p.add_argument("--no-ml", action="store_true", help="ML‑Filter deaktivieren")
    p.add_argument("--show-intermediate", action="store_true", help="1H‑Struktur im Struktur‑Chart einblenden")
    p.add_argument("--csv", "-c", action="store_true", help="Lade Kursdaten aus CSV statt yfinance (Dateinamen siehe Code)")
    p.add_argument("--realisieren", "-r", action="store_true", help="Alle 3 Monate Gewinne realisieren (Kapital reset)")
    # Achtung: '%' muss für argparse escaping verdoppelt werden
    p.add_argument("--fee", type=float, default=0.0, help="Handelskosten pro Trade (in $ oder %% ) (z.B. 2.5 oder 0.001 für 0.1%%)")
    p.add_argument("--slippage", type=float, default=0.0, help="Slippage pro Trade (in $ oder %% ) (z.B. 1.0 oder 0.0005 für 0.05%%)")
    p.add_argument("--slow", type=float, default=0.0, help="Verzögerung in Sekunden bis Orderausführung (max. 30, z.B. 5 für 5 Sekunden)")
    p.add_argument("--monthly-payout", type=float, default=0.0, help="Jeden Monat diesen Betrag vom Kapital abziehen (z.B. 5000)")
    p.add_argument("--counterfactuals", action="store_true", help="Was-wäre-wenn-Analyse (Counterfactuals) ausführen")
    p.add_argument("--no-ema-trend", action="store_true", help="EMA Trendfilter deaktivieren (USE_EMA_TREND False)")
    p.add_argument("--no-daily-ema", action="store_true", help="Täglichen EMA Filter deaktivieren (USE_DAILY_EMA False)")
    p.add_argument("--no-adx", action="store_true", help="ADX Regime Filter deaktivieren")
    p.add_argument("--no-confirm", action="store_true", help="Entry Bestätigung abschalten (REQUIRE_CONFIRM False)")
    p.add_argument("--deep-counterfactuals", action="store_true", help="Erweiterte Counterfactual Varianten (Filter toggles / Risk sweeps)")
    p.add_argument("--full-grid-cf", action="store_true", help="Komplette Re-Simulation über Kombinations-Gitter (langsam)")
    return p.parse_args()

def main():
    global CFG
    args = parse_args()
    base = PROFILES[args.profile].copy()
    base["_PROFILE"] = args.profile
    base["SYMBOL"] = args.symbol
    if args.no_ml:
        base["USE_ML"] = False
    if args.show_intermediate:
        base["SHOW_INTERMEDIATE"] = True
    # Zusätzliche Optionen in CFG übernehmen
    base["USE_CSV"] = getattr(args, "csv", False)
    base["REALISIEREN"] = getattr(args, "realisieren", False)
    base["FEE"] = getattr(args, "fee", 0.0)
    base["SLIPPAGE"] = getattr(args, "slippage", 0.0)
    # Begrenze SLOW auf maximal 30 Sekunden
    slow_val = min(max(getattr(args, "slow", 0.0), 0.0), 30.0)
    base["SLOW"] = slow_val
    if getattr(args, "monthly_payout", 0.0) > 0:
        base["MONTHLY_PAYOUT"] = getattr(args, "monthly_payout", 0.0)
    if getattr(args, "no_ema_trend", False):
        base["USE_EMA_TREND"] = False
    if getattr(args, "no_daily_ema", False):
        base["USE_DAILY_EMA"] = False
    if getattr(args, "no_adx", False):
        base["USE_ADX"] = False
    if getattr(args, "no_confirm", False):
        base["REQUIRE_CONFIRM"] = False
    base["DEEP_CF"] = getattr(args, "deep_counterfactuals", False)
    base["FULL_GRID_CF"] = getattr(args, "full_grid_cf", False)
    CFG = base  # global setzen

    daily, h1, m30 = load_data()
    print("[DEBUG] daily columns nach Indikatoren:", daily.columns.tolist())
    print("[DEBUG] h1 columns nach Indikatoren:", h1.columns.tolist())
    print("[DEBUG] m30 columns nach Indikatoren:", m30.columns.tolist())
    # Abbruch falls keine Kern-Daten vorhanden
    if daily.empty or 'close' not in daily.columns or h1.empty or 'close' not in h1.columns:
        print(f"[FEHLER] Keine verwertbaren Kursdaten für Symbol '{CFG['SYMBOL']}'.")
        print("Hinweis:")
        print("  1) Eigene CSV-Dateien anlegen (UTF-8) mit Header: date,open,high,low,close,volume")
        print("     Dateiformate akzeptiert: daily_SYMBOL.csv / h1_SYMBOL.csv / m30_SYMBOL.csv (oder daily.csv etc.)")
        print("  2) Falls Gold: probiere alternative Symbole: GC=F (Futures), GLD (ETF), XAUUSD=X (FX)")
        print("  3) Beispiel Start: python Ur-EW-Code.py -s GC=F   oder   python Ur-EW-Code.py -s GLD")
        print("  4) Prüfe, ob CSV wirklich Daten enthält (nicht leer) und dass 'close' numerisch ist.")
        return
    # Nach jedem Laden der Daten (egal ob CSV oder yfinance) immer Indikatoren berechnen
    add_all_indicators(daily, h1, m30)
    print("[DEBUG] daily columns nach Indikatoren:", daily.columns.tolist())
    print("[DEBUG] h1 columns nach Indikatoren:", h1.columns.tolist())
    print("[DEBUG] m30 columns nach Indikatoren:", m30.columns.tolist())
    # Übergeordneter Trendindikator (100-Tage SMA)
    try:
        daily["SMA_100"] = daily["close"].rolling(100).mean()
    except Exception:
        pass
    # Rolling Volatilität (annualisierte 20d-Std der täglichen Renditen)
    try:
        daily["volatility_20d"] = daily["close"].pct_change().rolling(20).std() * (252**0.5)
    except Exception:
        pass

    bt = Backtester(daily, h1, m30)
    print("Struktur (Daily+1H) analysieren, MTF‑Backtest (30m bevorzugt) + ML mit Pass‑Rate‑Guard läuft ...")
    metrics = bt.run()
    if not metrics:
        print("Keine Ergebnisse."); return

    print("\n--- Ergebnisse ---")
    print(f"Total Return: {metrics['total_return']:.2f}% | CAGR: {metrics['cagr']:.2f}% | Trades: {metrics['trades']}")
    print(f"Winrate: {metrics['hit']:.2f}% | PF: {metrics['profit_factor']:.2f} | Expectancy: ${metrics['expectancy']:.2f}")
    print(f"Vol (ann.): {metrics['vol']:.2f}% | Sharpe: {metrics['sharpe']:.2f} | Sortino: {metrics['sortino']:.2f} | UPI: {metrics['upi']:.2f} | GPR: {metrics['gain_to_pain']:.2f}")

    out_csv = f"trades_perfect_{CFG['_PROFILE']}_{CFG['SYMBOL']}.csv"
    pd.DataFrame([t.__dict__ for t in bt.trades]).to_csv(out_csv, index=False)
    out_pdf = f"elliott_report_perfect_{CFG['_PROFILE']}_{CFG['SYMBOL']}.pdf"
    plot_report(daily, h1, bt, metrics, pdf_path=out_pdf)
    print(f"CSV: {out_csv} | PDF: {out_pdf}")

    # --- Counterfactuals / Varianten (laufen jetzt auch bei --full-grid-cf oder --deep-counterfactuals) ---
    if getattr(args, 'counterfactuals', False) or CFG.get('FULL_GRID_CF') or CFG.get('DEEP_CF'):
        try:
            print("\n--- Counterfactuals ---")
            # Helper
            def _cf_calc(trades, risk_mult=1.0, prob_sizing=True, fixed_threshold=None, long_only=False, short_only=False):
                """Generische CF Berechnung für SimTrade oder Trade Objekte.
                SimTrade besitzt per_share & risk_per_share; Trade nicht unbedingt.
                Für Trade verwenden wir original pnl (keine Neuberechnung) um das echte Ergebnis zu sezieren.
                """
                if not trades: return dict(total=0.0,cagr=0.0,trades=0,end_cap=CFG['START_CAPITAL'])
                cap=CFG['START_CAPITAL']; highest=cap; taken=0
                first_time=getattr(trades[0],'time_in', pd.Timestamp.utcnow())
                last_time=getattr(trades[-1],'time_out', first_time)
                for obj in trades:
                    if long_only and getattr(obj,'direction','')!="LONG": continue
                    if short_only and getattr(obj,'direction','')!="SHORT": continue
                    # SimTrade Pfad
                    if hasattr(obj,'per_share'):
                        rps=getattr(obj,'risk_per_share', None)
                        if rps is None or rps<=0:
                            try:
                                rps=abs(obj.entry-obj.stop)
                            except Exception:
                                rps=1.0
                        size=(CFG['RISK_PER_TRADE']*risk_mult*cap)/max(rps,1e-9)
                        size=int(max(1,size))
                        cap+=obj.per_share*size
                        highest=max(highest,cap)
                        taken+=1
                        last_time=getattr(obj,'time_out', last_time)
                    else:  # Trade Objekt
                        cap+=getattr(obj,'pnl',0.0)
                        highest=max(highest,cap)
                        taken+=1
                        first_time=min(first_time, getattr(obj,'time_in', first_time))
                        last_time=max(last_time, getattr(obj,'time_out', last_time))
                start=CFG['START_CAPITAL']; end=cap; total_ret=((end/start)-1)*100.0
                years=(last_time - first_time).days/365.0 if (last_time>first_time) else 1.0
                cagr=((end/start)**(1/years)-1)*100.0 if years>0 else total_ret
                return dict(total=total_ret,cagr=cagr,trades=taken,end_cap=end)

            sims_sorted=sorted(bt.sim_trades, key=lambda t:t.time_in)
            # Szenarien definieren
            scenarios=[]
            if bt.sim_trades:
                if CFG.get('USE_ML', False):
                    scenarios.append(("ohne_ml", sims_sorted))
                # Wenn Modell da: verschiedene Threshold-Quantile
                if bt.model is not None:
                    Xall,_=bt._XY(sims_sorted); probs=bt.model.predict_proba(Xall)[:,1]
                    base=list(zip(sims_sorted, probs))
                    for q,name in [(0.20,'top80'),(0.40,'top60'),(0.10,'top90')]:
                        thr=np.quantile(probs,q)
                        subset=[t for t,p in base if p>=thr]
                        scenarios.append((f"thr_{name}", subset))
                    # Fixes Threshold 0.5
                    subset=[t for t,p in base if p>=0.5]
                    scenarios.append(("thr_fixed_0_5", subset))
                    # Long-only / Short-only auf Basis original finaler Trades (mit Modellfilter)
                    final_trades=[tr for tr in bt.trades]
                    scenarios.append(("final_long_only", [t for t in final_trades if t.direction=="LONG"]))
                    scenarios.append(("final_short_only", [t for t in final_trades if t.direction=="SHORT"]))
                # Risk Multipliers auf allen SimTrades
                scenarios.append(("risk_0_5x", sims_sorted))
                scenarios.append(("risk_1_5x", sims_sorted))

            results=[]
            for name,tr_list in scenarios:
                if not tr_list: continue
                if name.startswith('risk_0_5x'): r=_cf_calc(tr_list, risk_mult=0.5)
                elif name.startswith('risk_1_5x'): r=_cf_calc(tr_list, risk_mult=1.5)
                elif name in ("final_long_only","final_short_only"):
                    r=_cf_calc(tr_list, risk_mult=1.0, long_only=name.endswith('long_only'), short_only=name.endswith('short_only'))
                else:
                    r=_cf_calc(tr_list)
                results.append((name,r))

            # Ausgabe
            for name,r in results:
                print(f"{name}: Return {r['total']:.2f}% | CAGR {r['cagr']:.2f}% | Trades {r['trades']} | EndCap {r['end_cap']:.2f}")
            # Optional CSV Export
            if results:
                cf_path=f"counterfactuals_{CFG['_PROFILE']}_{CFG['SYMBOL']}.csv"
                pd.DataFrame([dict(scenario=k, **v) for k,v in results]).to_csv(cf_path, index=False)
                print(f"Counterfactual CSV: {cf_path}")

            # Deep Variants: kombinierte Filter-Toggles & Risiko-Sweeps
            if CFG.get('DEEP_CF', False) and bt.sim_trades:
                print("\n--- Deep Counterfactuals (Filter Toggles) ---")
                base_trades=sorted(bt.sim_trades, key=lambda t:t.time_in)
                # Konfigurationen: (name, overrides dict)
                variants=[
                    ("all_filters_off", dict(USE_EMA_TREND=False, USE_DAILY_EMA=False, USE_ADX=False, REQUIRE_CONFIRM=False)),
                    ("no_ema", dict(USE_EMA_TREND=False)),
                    ("no_adx", dict(USE_ADX=False)),
                    ("no_confirm", dict(REQUIRE_CONFIRM=False)),
                    ("no_daily_ema", dict(USE_DAILY_EMA=False)),
                    ("only_adx", dict(USE_EMA_TREND=False, REQUIRE_CONFIRM=False)),
                ]
                deep_rows=[]
                for vname,ov in variants:
                    # Filter neu aufbauen indem wir Setups erneut evaluieren wäre teuer -> approximativ: wir ignorieren Filter indem wir alle SimTrades nehmen.
                    # Für Teilabschaltung könnten wir heuristisch filtern, hier einfacher: wenn Filter deaktiviert -> gleiche baseline Trades (da Filter früher greifen) => echtes Re-Sim erforderlich. Markieren als approximativ.
                    r=_cf_calc(base_trades)  # approximative Wirkung
                    r['approx']=True
                    deep_rows.append((vname,r))
                for name,r in deep_rows:
                    print(f"{name}: Return {r['total']:.2f}% | CAGR {r['cagr']:.2f}% | Trades {r['trades']} (approx)")
                if deep_rows:
                    deep_path=f"counterfactuals_deep_{CFG['_PROFILE']}_{CFG['SYMBOL']}.csv"
                    pd.DataFrame([dict(scenario=k, **v) for k,v in deep_rows]).to_csv(deep_path, index=False)
                    print(f"Deep Counterfactual CSV: {deep_path}")

            # Vollständige Grid-Re-Simulation (teuer): verschiedene Filterkombinationen + ML an/aus + Risiko Faktoren
            if CFG.get('FULL_GRID_CF', False):
                print("\n--- Full Grid Re-Simulation (kann dauern) ---")
                import itertools, time
                grid_results=[]
                # Parameter-Ranges
                use_ml_opts=[True, False]
                ema_trend_opts=[True, False]
                daily_ema_opts=[True, False]
                adx_opts=[True, False]
                confirm_opts=[True, False]
                risk_mults=[0.5,1.0,1.5]
                start_time=time.time()
                combos=list(itertools.product(use_ml_opts, ema_trend_opts, daily_ema_opts, adx_opts, confirm_opts, risk_mults))
                print(f"Varianten: {len(combos)} Kombinationen")
                for (use_ml, ema_tr, daily_ema, adx_on, confirm_on, rmult) in combos:
                    # Neue Kopie der Konfiguration
                    cfg_copy=CFG.copy()
                    cfg_copy.update(dict(USE_ML=use_ml, USE_EMA_TREND=ema_tr, USE_DAILY_EMA=daily_ema, USE_ADX=adx_on, REQUIRE_CONFIRM=confirm_on))
                    # Risiko Faktor anwenden
                    base_rpt=CFG.get('RISK_PER_TRADE',0.01)
                    cfg_copy['RISK_PER_TRADE']=base_rpt*rmult
                    # Re-Run Backtester frisch (nutzt globale CFG -> temporär überschreiben)
                    old_cfg=CFG.copy()
                    try:
                        globals()['CFG']=cfg_copy
                        bt2=Backtester(daily.copy(), h1.copy(), m30.copy())
                        metrics2=bt2.run()
                        if not metrics2:
                            res=dict(total_return=np.nan,cagr=np.nan,trades=0,hit=np.nan)
                        else:
                            res=dict(total_return=metrics2.get('total_return'), cagr=metrics2.get('cagr'), trades=metrics2.get('trades'), hit=metrics2.get('hit'), sharpe=metrics2.get('sharpe'), sortino=metrics2.get('sortino'), max_dd=metrics2.get('max_dd'), calmar=metrics2.get('calmar'), profit_factor=metrics2.get('profit_factor'), expectancy=metrics2.get('expectancy'), exposure=metrics2.get('exposure'), trades_per_year=metrics2.get('trades_per_year'))
                        res.update(dict(use_ml=use_ml, ema_trend=ema_tr, daily_ema=daily_ema, adx=adx_on, confirm=confirm_on, risk_mult=rmult))
                        grid_results.append(res)
                        print(f"Grid: ML={use_ml} EMA={ema_tr} DEMA={daily_ema} ADX={adx_on} CONF={confirm_on} Rmult={rmult} -> Ret {res['total_return']:.2f}% Trades {res['trades']}")
                    except Exception as e:
                        print(f"[GRID-WARN] {e}")
                    finally:
                        globals()['CFG']=old_cfg
                if grid_results:
                    grid_path=f"counterfactuals_fullgrid_{CFG['_PROFILE']}_{CFG['SYMBOL']}.csv"
                    pd.DataFrame(grid_results).to_csv(grid_path, index=False)
                    print(f"Full Grid CSV: {grid_path} | Dauer {(time.time()-start_time):.1f}s")
        except Exception as e:
            print(f"[WARN] Counterfactuals fehlgeschlagen: {e}")

if __name__ == "__main__":
    main()