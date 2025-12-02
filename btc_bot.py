import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
import numpy as np

# --- 1. 全局配置 ---
st.set_page_config(
    page_title="PolySniper Pro (US)",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 注入
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .stMetric { background-color: #1A1C24; border: 1px solid #2E303E; border-radius: 8px; padding: 15px; }
    [data-testid="stMetricValue"] { font-family: 'SF Mono', monospace; font-size: 26px; }
    .disclaimer { font-size: 12px; color: #555; text-align: center; margin-top: 50px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据引擎 (切换为 Kraken 以适配美国服务器) ---
@st.cache_resource
def init_exchange():
    # 使用 Kraken 交易所，因为它允许美国 IP (Streamlit Server) 访问
    return ccxt.kraken({'enableRateLimit': True})

def fetch_data_robust():
    start_time = time.time()
    exchange = init_exchange()
    symbol = 'BTC/USD'  # Kraken 使用 USD 交易对
    try:
        ticker = exchange.fetch_ticker(symbol)
        
        # Kraken 的 K 线获取逻辑
        bars_15m = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=60)
        bars_3m = exchange.fetch_ohlcv(symbol, timeframe='3m', limit=30)
        
        df_15m = pd.DataFrame(bars_15m, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
        df_15m['ts'] = pd.to_datetime(df_15m['ts'], unit='ms')
        
        df_3m = pd.DataFrame(bars_3m, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
        df_3m['ts'] = pd.to_datetime(df_3m['ts'], unit='ms')
        
        df_15m['tr'] = df_15m[['high', 'low', 'close']].apply(lambda x: max(x['high']-x['low'], abs(x['high']-x['close']), abs(x['low']-x['close'])), axis=1)
        df_15m['ATR'] = df_15m['tr'].rolling(14).mean()
        
        latency = (time.time() - start_time) * 1000
        return ticker['last'], df_15m, df_3m, latency, None
    except Exception as e:
        return None, None, None, 0, str(e)

# --- 3. 核心计算逻辑 ---
def calculate_analytics(price, df_15m, df_3m, mins_left, poly_yes, poly_no):
    curr = df_15m.iloc[-1]
    open_price = curr['open']
    atr = df_15m.iloc[-2]['ATR'] if pd.notnull(df_15m.iloc[-2]['ATR']) else price * 0.005
    gap = price - open_price
    
    score = 50
    score += (gap / atr) * 30 
    
    start_time = curr['ts']
    micro = df_3m[df_3m['ts'] >= start_time]
    green = sum(micro['close'] > micro['open'])
    red = sum(micro['close'] < micro['open'])
    
    if green > red: score += 10
    elif red > green: score -= 10
    
    if mins_left < 5: score += (gap / atr) * 20
    
    ai_prob = max(1, min(99, score))
    
    win_prob = ai_prob / 100.0
    if ai_prob > 50:
        cost = poly_yes / 100.0
        ev = (win_prob * (1 - cost)) - ((1 - win_prob) * cost)
        direction = "YES (看涨)"
    else:
        lose_prob = (100 - ai_prob) / 100.0
        cost = poly_no / 100.0
        ev = (lose_prob * (1 - cost)) - ((1 - lose_prob) * cost)
        direction = "NO (看跌)"
        
    return ai_prob, ev, gap, open_price, direction

# --- 4. 界面布局 ---
with st.sidebar:
    st.markdown("## 🦅 PolySniper Pro")
    st.caption("Data Source: Kraken (US Compatible)")
    st.divider()
    col_s1, col_s2 = st.columns(2)
    with col_s1: poly_yes = st.number_input("YES Price (¢)", 1, 99, 65)
    with col_s2: poly_no = st.number_input("NO Price (¢)", 1, 99, 35)
    st.divider()
    run_app = st.toggle("Live Data Stream", value=True)
    status_ph = st.empty()
    if run_app: status_ph.success("● Online")
    else: status_ph.warning("○ Offline")

st.title("🦅 PolySniper 机构级终端")

ph_error = st.empty()
ph_latency = st.empty()
ph_dash = st.empty()
ph_chart = st.empty()

st.markdown("""
    <div class="disclaimer">
    ⚠️ <b>风险提示：</b> 本工具仅用于辅助决策。数据源已切换为 Kraken 以适配美国服务器环境。
    </div>
""", unsafe_allow_html=True)

if run_app:
    while True:
        price, df_15m, df_3m, latency, error_msg = fetch_data_robust()
        
        if error_msg:
            ph_error.error(f"连接重试中: {error_msg}")
            time.sleep(3)
            continue
        else:
            ph_error.empty()

        if price is not None:
            now = datetime.now()
            mins_passed = now.minute % 15
            mins_left = 15 - mins_passed
            secs_left = 60 - now.second
            
            ai_prob, ev, gap, open_price, direction = calculate_analytics(
                price, df_15m, df_3m, mins_left, poly_yes, poly_no
            )
            
            color_lat = "#00C851" if latency < 800 else "#ffbb33"
            ph_latency.markdown(f"""
            <div style="font-size:12px; color:#666; margin-bottom:10px;">
                📡 Data Source: Kraken | Latency: <b style="color:{color_lat}">{latency:.0f}ms</b>
            </div>
            """, unsafe_allow_html=True)

            with ph_dash.container():
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("倒计时", f"{mins_left-1}:{secs_left:02d}")
                c2.metric("BTC 现价", f"${price:,.2f}")
                c3.metric("Gap", f"${gap:+.2f}", delta_color="off")
                prob_color = "normal" if ai_prob > 50 else "inverse"
                c4.metric("AI 胜率", f"{ai_prob:.1f}%", delta=direction, delta_color=prob_color)
                ev_label = "建议下注" if ev > 0.05 else "建议观望"
                c5.metric("EV 期望", f"{ev:+.2f}", delta=ev_label)

            with ph_chart.container():
                fig = make_subplots(rows=1, cols=1)
                fig.add_trace(go.Candlestick(
                    x=df_3m['ts'], open=df_3m['open'], high=df_3m['high'], low=df_3m['low'], close=df_3m['close'],
                    name="3m K-Line", increasing_line_color='#00C851', decreasing_line_color='#ff4444'
                ))
                fig.add_hline(y=open_price, line_color="#33b5e5", line_width=2, annotation_text="OPEN")
                fig.add_hline(y=price, line_color="#ffbb33", line_width=1, line_dash="dot", annotation_text="NOW")
                fig.update_layout(
                    height=500, margin=dict(l=0, r=0, t=30, b=0), xaxis_rangeslider_visible=False, template="plotly_dark",
                    title={'text': f"Micro Structure: Gap ${gap:+.2f}", 'y':0.95, 'x':0.5, 'xanchor': 'center'},
                    uirevision='constant'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        time.sleep(1)
