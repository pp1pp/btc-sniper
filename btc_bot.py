{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import ccxt\
import pandas as pd\
import plotly.graph_objects as go\
from plotly.subplots import make_subplots\
import time\
from datetime import datetime\
import numpy as np\
\
# --- 1. \uc0\u20840 \u23616 \u37197 \u32622 \u19982 \u39029 \u38754 \u21021 \u22987 \u21270  ---\
st.set_page_config(\
    page_title="PolySniper Pro | \uc0\u26426 \u26500 \u32423 \u39044 \u27979 \u32456 \u31471 ",\
    page_icon="\uc0\u55358 \u56709 ",\
    layout="wide",\
    initial_sidebar_state="expanded",\
    menu_items=\{\
        'Get Help': 'https://www.google.com',\
        'Report a bug': "https://github.com",\
        'About': "PolySniper Pro v1.0 - BTC 15min \uc0\u30424 \u21475 \u21338 \u24328 \u31995 \u32479 "\
    \}\
)\
\
# \uc0\u27880 \u20837 \u19987 \u19994 \u32423  CSS (\u38544 \u34255 \u40664 \u35748 \u33756 \u21333 \u65292 \u32654 \u21270 \u23383 \u20307 )\
st.markdown("""\
    <style>\
    /* \uc0\u38544 \u34255  Streamlit \u40664 \u35748 \u27721 \u22561 \u33756 \u21333 \u21644 \u39029 \u33050  */\
    #MainMenu \{visibility: hidden;\}\
    footer \{visibility: hidden;\}\
    \
    /* \uc0\u32039 \u20945 \u24067 \u23616  */\
    .block-container \{ padding-top: 1rem; padding-bottom: 2rem; \}\
    \
    /* \uc0\u25968 \u25454 \u21345 \u29255 \u26679 \u24335  */\
    .stMetric \{ \
        background-color: #1A1C24; \
        border: 1px solid #2E303E; \
        border-radius: 8px; \
        padding: 15px; \
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);\
    \}\
    [data-testid="stMetricValue"] \{ \
        font-family: 'SF Mono', 'Roboto Mono', monospace; \
        font-size: 26px; \
        font-weight: 600;\
    \}\
    [data-testid="stMetricLabel"] \{ font-size: 14px; color: #8F9BB3; \}\
    \
    /* \uc0\u24213 \u37096 \u20813 \u36131 \u22768 \u26126  */\
    .disclaimer \{ font-size: 12px; color: #555; text-align: center; margin-top: 50px; \}\
    </style>\
""", unsafe_allow_html=True)\
\
# --- 2. \uc0\u20581 \u22766 \u30340 \u25968 \u25454 \u24341 \u25806  (\u24102 \u37325 \u35797 \u26426 \u21046 ) ---\
@st.cache_resource\
def init_exchange():\
    return ccxt.binance(\{'enableRateLimit': True\})\
\
def fetch_data_robust():\
    """\
    \uc0\u29983 \u20135 \u32423 \u25968 \u25454 \u33719 \u21462 \u65306 \u21253 \u21547 \u38169 \u35823 \u22788 \u29702 \u21644 \u33258 \u21160 \u37325 \u35797 \
    """\
    start_time = time.time()\
    exchange = init_exchange()\
    try:\
        # \uc0\u33719 \u21462  Ticker\
        ticker = exchange.fetch_ticker('BTC/USDT')\
        \
        # \uc0\u33719 \u21462  K \u32447  (15m & 3m)\
        bars_15m = exchange.fetch_ohlcv('BTC/USDT', timeframe='15m', limit=60)\
        bars_3m = exchange.fetch_ohlcv('BTC/USDT', timeframe='3m', limit=30)\
        \
        # \uc0\u25968 \u25454 \u28165 \u27927 \
        df_15m = pd.DataFrame(bars_15m, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])\
        df_15m['ts'] = pd.to_datetime(df_15m['ts'], unit='ms')\
        \
        df_3m = pd.DataFrame(bars_3m, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])\
        df_3m['ts'] = pd.to_datetime(df_3m['ts'], unit='ms')\
        \
        # \uc0\u35745 \u31639 \u25351 \u26631 \
        df_15m['tr'] = df_15m[['high', 'low', 'close']].apply(lambda x: max(x['high']-x['low'], abs(x['high']-x['close']), abs(x['low']-x['close'])), axis=1)\
        df_15m['ATR'] = df_15m['tr'].rolling(14).mean()\
        \
        latency = (time.time() - start_time) * 1000\
        return ticker['last'], df_15m, df_3m, latency, None # None \uc0\u20195 \u34920 \u26080 \u38169 \u35823 \
    except Exception as e:\
        # \uc0\u36820 \u22238 \u38169 \u35823 \u20449 \u24687 \u65292 \u32780 \u19981 \u26159 \u30452 \u25509 \u23849 \u28291 \
        return None, None, None, 0, str(e)\
\
# --- 3. \uc0\u26680 \u24515 \u19994 \u21153 \u36923 \u36753  ---\
def calculate_analytics(price, df_15m, df_3m, mins_left, poly_yes, poly_no):\
    curr = df_15m.iloc[-1]\
    open_price = curr['open']\
    \
    # \uc0\u38450 \u27490  ATR \u20026 \u31354  (\u21018 \u21551 \u21160 \u26102 )\
    atr = df_15m.iloc[-2]['ATR'] if pd.notnull(df_15m.iloc[-2]['ATR']) else price * 0.005\
    gap = price - open_price\
    \
    # --- \uc0\u31639 \u27861 \u27169 \u22411  ---\
    score = 50\
    score += (gap / atr) * 30 # \uc0\u36317 \u31163 \u26435 \u37325 \
    \
    # \uc0\u24494 \u35266 \u32467 \u26500 \
    start_time = curr['ts']\
    micro = df_3m[df_3m['ts'] >= start_time]\
    green = sum(micro['close'] > micro['open'])\
    red = sum(micro['close'] < micro['open'])\
    \
    if green > red: score += 10\
    elif red > green: score -= 10\
    \
    # \uc0\u26102 \u38388 \u34928 \u20943 \
    if mins_left < 5: score += (gap / atr) * 20\
    \
    ai_prob = max(1, min(99, score))\
    \
    # EV \uc0\u35745 \u31639 \
    win_prob = ai_prob / 100.0\
    if ai_prob > 50:\
        cost = poly_yes / 100.0\
        ev = (win_prob * (1 - cost)) - ((1 - win_prob) * cost)\
        direction = "YES (\uc0\u30475 \u28072 )"\
    else:\
        lose_prob = (100 - ai_prob) / 100.0\
        cost = poly_no / 100.0\
        # \uc0\u20570 \u31354 \u26102 \u65292 \u25105 \u20204 \u30340 \u33719 \u32988 \u27010 \u29575 \u26159  lose_prob\
        ev = (lose_prob * (1 - cost)) - ((1 - lose_prob) * cost)\
        direction = "NO (\uc0\u30475 \u36300 )"\
        \
    return ai_prob, ev, gap, open_price, direction\
\
# --- 4. \uc0\u20391 \u36793 \u26639  (\u25511 \u21046 \u21488 ) ---\
with st.sidebar:\
    st.markdown("## \uc0\u55358 \u56709  PolySniper Pro")\
    st.caption("v1.2.0 | Stable Build")\
    \
    st.divider()\
    \
    st.markdown("### \uc0\u55357 \u56496  \u24066 \u22330 \u25968 \u25454 \u24405 \u20837 ")\
    col_s1, col_s2 = st.columns(2)\
    with col_s1:\
        poly_yes = st.number_input("YES \uc0\u20215 \u26684  (\'a2)", 1, 99, 65)\
    with col_s2:\
        poly_no = st.number_input("NO \uc0\u20215 \u26684  (\'a2)", 1, 99, 35)\
        \
    st.divider()\
    \
    # \uc0\u31995 \u32479 \u29366 \u24577 \u30417 \u25511 \
    st.markdown("### \uc0\u55357 \u56741 \u65039  \u31995 \u32479 \u29366 \u24577 ")\
    run_app = st.toggle("\uc0\u36830 \u25509 \u20132 \u26131 \u25152 \u25968 \u25454 \u27969 ", value=True)\
    status_ph = st.empty()\
    \
    if run_app:\
        status_ph.success("\uc0\u9679  \u22312 \u32447  (Online)")\
    else:\
        status_ph.warning("\uc0\u9675  \u31163 \u32447  (Offline)")\
\
# --- 5. \uc0\u20027 \u24037 \u20316 \u21306  ---\
st.title("\uc0\u55358 \u56709  PolySniper \u26426 \u26500 \u32423 \u32456 \u31471 ")\
\
# \uc0\u21344 \u20301 \u31526 \u23481 \u22120 \u21021 \u22987 \u21270 \
ph_error = st.empty()   # \uc0\u38169 \u35823 \u28040 \u24687 \u26639 \
ph_latency = st.empty() # \uc0\u24310 \u36831 \u30417 \u25511 \
ph_dash = st.empty()    # \uc0\u20202 \u34920 \u30424 \
ph_chart = st.empty()   # \uc0\u22270 \u34920 \
\
# \uc0\u24213 \u37096 \u20813 \u36131 \u22768 \u26126 \
st.markdown("""\
    <div class="disclaimer">\
    \uc0\u9888 \u65039  <b>\u39118 \u38505 \u25552 \u31034 \u65306 </b> \u26412 \u24037 \u20855 \u20165 \u29992 \u20110 \u25968 \u25454 \u20998 \u26512 \u19982 \u36741 \u21161 \u20915 \u31574 \u65292 \u19981 \u26500 \u25104 \u20219 \u20309 \u25237 \u36164 \u24314 \u35758 \u12290 <br>\
    \uc0\u21152 \u23494 \u36135 \u24065 \u19982 \u39044 \u27979 \u24066 \u22330 \u23646 \u20110 \u39640 \u39118 \u38505 \u25237 \u36164 \u65292 \u35831 \u20005 \u26684 \u25511 \u21046 \u20179 \u20301 \u12290 EV \u35745 \u31639 \u22522 \u20110 \u21382 \u21490 \u27874 \u21160 \u29575 \u27169 \u22411 \u65292 \u19981 \u20195 \u34920 \u26410 \u26469 \u24517 \u28982 \u25910 \u30410 \u12290 \
    </div>\
""", unsafe_allow_html=True)\
\
if run_app:\
    while True:\
        # 1. \uc0\u33719 \u21462 \u25968 \u25454 \
        price, df_15m, df_3m, latency, error_msg = fetch_data_robust()\
        \
        if error_msg:\
            # \uc0\u20248 \u38597 \u30340 \u38169 \u35823 \u22788 \u29702 \
            ph_error.error(f"\uc0\u32593 \u32476 \u36830 \u25509 \u20013 \u26029 : \{error_msg\} | \u27491 \u22312 \u37325 \u35797 ...")\
            time.sleep(3) # \uc0\u26242 \u20572 3\u31186 \u20877 \u37325 \u35797 \u65292 \u38450 \u27490 \u27515 \u24490 \u29615 \u21047 \u23631 \
            continue\
        else:\
            ph_error.empty() # \uc0\u28165 \u38500 \u38169 \u35823 \u20449 \u24687 \
\
        if price is not None:\
            # 2. \uc0\u35745 \u31639 \u26102 \u38388 \
            now = datetime.now()\
            mins_passed = now.minute % 15\
            mins_left = 15 - mins_passed\
            secs_left = 60 - now.second\
            \
            # 3. \uc0\u26680 \u24515 \u35745 \u31639 \
            ai_prob, ev, gap, open_price, direction = calculate_analytics(\
                price, df_15m, df_3m, mins_left, poly_yes, poly_no\
            )\
            \
            # --- UI \uc0\u26356 \u26032  A: \u24310 \u36831  ---\
            color_lat = "#00C851" if latency < 800 else "#ffbb33"\
            ph_latency.markdown(f"""\
            <div style="font-size:12px; color:#666; margin-bottom:10px; display:flex; justify-content:space-between;">\
                <span>\uc0\u55357 \u56545  Binance Data Stream</span>\
                <span>Latency: <b style="color:\{color_lat\}">\{latency:.0f\}ms</b></span>\
            </div>\
            """, unsafe_allow_html=True)\
\
            # --- UI \uc0\u26356 \u26032  B: \u20202 \u34920 \u30424  ---\
            with ph_dash.container():\
                c1, c2, c3, c4, c5 = st.columns(5)\
                \
                c1.metric("\uc0\u9201 \u65039  \u32467 \u31639 \u20498 \u35745 \u26102 ", f"\{mins_left-1\}:\{secs_left:02d\}")\
                c2.metric("\uc0\u55357 \u56496  BTC \u29616 \u20215 ", f"$\{price:,.2f\}")\
                \
                # Gap \uc0\u21160 \u24577 \u39068 \u33394 \
                c3.metric("\uc0\u55357 \u56527  \u36317 \u31163 \u32988 \u36127 \u32447 ", f"$\{gap:+.2f\}", delta_color="off")\
                \
                # AI \uc0\u39044 \u27979 \
                prob_delta_color = "normal" if ai_prob > 50 else "inverse"\
                c4.metric("\uc0\u55358 \u56800  AI \u32988 \u29575 ", f"\{ai_prob:.1f\}%", delta=direction, delta_color=prob_delta_color)\
                \
                # EV \uc0\u26399 \u26395 \u20540  (\u26680 \u24515 )\
                ev_label = "\uc0\u9989  \u24314 \u35758 \u19979 \u27880 " if ev > 0.05 else "\u55357 \u57003  \u24314 \u35758 \u35266 \u26395 "\
                c5.metric("\uc0\u9878 \u65039  EV \u26399 \u26395 \u20540 ", f"\{ev:+.2f\}", delta=ev_label)\
\
            # --- UI \uc0\u26356 \u26032  C: \u19987 \u19994 \u22270 \u34920  ---\
            with ph_chart.container():\
                fig = make_subplots(rows=1, cols=1)\
                \
                # \uc0\u24494 \u35266  K \u32447 \
                fig.add_trace(go.Candlestick(\
                    x=df_3m['ts'], open=df_3m['open'], high=df_3m['high'], low=df_3m['low'], close=df_3m['close'],\
                    name="3m K-Line",\
                    increasing_line_color='#00C851', decreasing_line_color='#ff4444'\
                ))\
                \
                # \uc0\u20851 \u38190 \u20301 \
                fig.add_hline(y=open_price, line_color="#33b5e5", line_width=2, line_dash="solid", annotation_text="OPEN (\uc0\u32988 \u36127 \u32447 )")\
                fig.add_hline(y=price, line_color="#ffbb33", line_width=1, line_dash="dot", annotation_text="CURRENT")\
                \
                fig.update_layout(\
                    height=550,\
                    margin=dict(l=0, r=0, t=30, b=0),\
                    xaxis_rangeslider_visible=False,\
                    template="plotly_dark",\
                    title=\{\
                        'text': f"Micro-Battlefield: Gap $\{gap:+.2f\}",\
                        'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'\
                    \},\
                    font=dict(family="Roboto, monospace"),\
                    uirevision='constant_value' # \uc0\u38145 \u23450 \u32553 \u25918 \u65292 \u38450 \u27490 \u21047 \u26032 \u37325 \u32622 \
                )\
                st.plotly_chart(fig, use_container_width=True)\
        \
        # 0.5\uc0\u31186 \u24515 \u36339 \
        time.sleep(0.5)\
}