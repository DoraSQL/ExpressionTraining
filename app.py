"""
app.py - 《表達能力特訓 Agent》互動主程式
由 mia貓 專為 美女貓貓 打造 🐾✨
"""

import os
import json
import streamlit as st
from dotenv import load_dotenv

# 引入自訂題庫與提示詞
from prompts import (
    LEVELS,
    EQ_EVAL_PROMPT,
    EQ_MULTI_ROUND_PROMPT,
    SUMMARY_GEN_PROMPT,
    SUMMARY_EVAL_PROMPT,
    OFFLINE_STORIES
)

# 載入環境變數（若有 .env 檔）
load_dotenv()

# ==============================================================================
# 🎨 頁面外觀設定與可愛清新風格 CSS
# ==============================================================================
st.set_page_config(
    page_title="表達能力特訓 Agent 🐾",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* 主體字型與配色微調 */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ff6b81;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #57606f;
        margin-bottom: 1.2rem;
    }
    .stCard {
        background-color: #f8f9fa;
        border-radius: 14px;
        padding: 1.2rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        margin-bottom: 1rem;
    }
    .npc-box {
        background-color: #fff0f3;
        border-left: 5px solid #ff4757;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .mia-feedback {
        background-color: #f1f2f6;
        border-left: 5px solid #ffa502;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .magic-box {
        background-color: #e8f7ee;
        border-left: 5px solid #2ed573;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .counter-badge {
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🧠 AI 呼叫封裝（支援 Google Gemini 與離線體驗模式）
# ==============================================================================

import re

def get_gemini_client(api_key: str):
    """初始化 Gemini Client"""
    if not api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key.strip())
        return client
    except Exception as e:
        st.error(f"⚠️ 連線 Gemini 時遇到小狀況：{e}")
        return None

def get_available_models(client) -> list:
    """呼叫 Google ListModels，取得該 API Key 支援的所有真實可用文字生成模型"""
    if not client:
        return []
    try:
        available = []
        for m in client.models.list():
            actions = getattr(m, 'supported_actions', []) or []
            if not actions or 'generateContent' in actions:
                name = m.name
                if name.startswith('models/'):
                    name = name[len('models/'):]
                available.append(name)
        # 優先順序：含 flash 的模型排前
        available.sort(key=lambda x: (0 if 'flash' in x.lower() else 1, x))
        return available
    except Exception:
        return []

def call_gemini(client, prompt: str) -> str:
    """呼叫 Gemini 生成文字，具備動態模型探測與平滑降級機制"""
    if not client:
        return ""

    # 1. 動態探測當前 API Key 支援的可用模型清單
    if "available_models" not in st.session_state or not st.session_state.available_models:
        st.session_state.available_models = get_available_models(client)

    candidate_models = []
    preferred = st.session_state.get("active_gemini_model")
    if preferred:
        candidate_models.append(preferred)

    for m in st.session_state.get("available_models", []):
        if m not in candidate_models:
            candidate_models.append(m)

    fallback_defaults = [
        'gemini-2.0-flash',
        'gemini-2.0-flash-exp',
        'gemini-2.5-flash',
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-flash-002',
        'gemini-1.5-flash-001',
        'gemini-1.5-pro',
        'gemini-1.5-pro-latest',
        'gemini-pro'
    ]
    for m in fallback_defaults:
        if m not in candidate_models:
            candidate_models.append(m)

    last_err = None
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                st.session_state.active_gemini_model = model_name
                return response.text
        except Exception as e:
            last_err = e
            continue

    st.warning(f"⚠️ mia 貓在嘗試連線時遇到小阻礙（嘗試過的模型皆不可用）：\n{last_err}")
    return ""

def clean_json_response(raw_text: str) -> dict:
    """清洗並解析 AI 回傳的 JSON 字串，具備強韌的容錯抽取能力"""
    if not raw_text:
        raise ValueError("回傳內容為空")
    text = raw_text.strip()
    # 1. 嘗試直接解析
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # 2. 嘗試提取 ```json ... ``` 區塊
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if code_block:
        try:
            return json.loads(code_block.group(1).strip())
        except Exception:
            pass

    # 3. 嘗試提取最外層的大括號 { ... }
    brace_block = re.search(r"(\{[\s\S]*\})", text)
    if brace_block:
        try:
            return json.loads(brace_block.group(1).strip())
        except Exception:
            pass

    raise ValueError(f"無法解析 JSON 格式：\n{raw_text}")

def get_round_hint(level: dict, round_num: int, chat_history: list) -> str:
    """獲取指定回合的 mia 貓拆招錦囊提示（支援 AI 動態生成與離線題庫雙重備援）"""
    # 1. 若 round_num > 1，優先檢查上一回合 AI 或 mock 評測給出的 next_round_hint
    if round_num > 1 and chat_history:
        prev_eval = chat_history[-1].get("eval_data", {})
        ai_hint = prev_eval.get("next_round_hint", "").strip()
        if ai_hint:
            return ai_hint
    
    # 2. 查找 offline_rounds 中對應 round 的 hint
    offline_rounds = level.get("offline_rounds", [])
    for r_data in offline_rounds:
        if r_data.get("round") == round_num:
            r_hint = r_data.get("hint", "").strip()
            if r_hint:
                return r_hint
                
    # 3. 若為第 1 回合，使用 level['hint']
    if round_num == 1 and level.get("hint"):
        return level.get("hint")
        
    return "保持真誠與同理心，先肯定對方的感受，再溫柔且堅定地表達自己的想法喔！🐾"

# ==============================================================================
# 🐾 側邊欄設定（身分與模式選單）
# ==============================================================================

with st.sidebar:
    st.markdown("### 🐾 特訓基地控制台")
    st.markdown("👑 **學員**：美女貓貓")
    st.markdown("🐱 **專屬教練**：mia貓")
    st.divider()

    # API Key 輸入區
    default_key = os.getenv("GEMINI_API_KEY", "")
    if not default_key:
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                default_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

    user_api_key = st.text_input(
        "🔑 Gemini API Key（選填）：",
        value=default_key,
        type="password",
        help="輸入你的 Gemini API Key；若沒有，系統會啟動【免 Key 智慧模擬演練模式】，依然能正常練習喔！"
    )

    client = get_gemini_client(user_api_key)
    if client:
        if "available_models" not in st.session_state or not st.session_state.available_models:
            st.session_state.available_models = get_available_models(client)
        detected = st.session_state.get("available_models", [])
        if detected:
            active_m = st.session_state.get("active_gemini_model", detected[0])
            st.success(f"🟢 AI 大腦在線中！已匹配：`{active_m}`")
        else:
            st.success("🟢 AI 大腦在線中！（具備自動容錯降級）")
    else:
        st.info("🟡 模式：【免 Key 智慧模擬體驗】（不需 API Key 也能玩）")

    st.divider()

    mode = st.radio(
        "🎯 選擇今日特訓項目：",
        ["🎮 模式一：高情商闖關大冒險", "📝 模式二：150字長話短說練功房"],
        index=0
    )

    st.divider()
    st.markdown("💡 **小撇步**：每次練習後，仔細看 mia 貓的「魔法變身示範」，模仿大師的句型是進步最快的方法喔！")

# ==============================================================================
# 🎮 模式一：高情商闖關大冒險
# ==============================================================================

if mode == "🎮 模式一：高情商闖關大冒險":
    st.markdown('<div class="main-title">🎮 高情商闖關大冒險</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">像打 RPG 遊戲一樣升級打怪！學習接招拆招、優雅拒絕、化解尷尬～</div>', unsafe_allow_html=True)

    # 關卡選擇器
    level_names = [f"第 {lvl['id']} 關：{lvl['name'].split('：')[-1]}" for lvl in LEVELS]
    selected_idx = st.selectbox("🚩 選擇你要挑戰的關卡：", range(len(LEVELS)), format_func=lambda i: level_names[i])
    current_level = LEVELS[selected_idx]

    # 關卡資訊卡片
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### {current_level['name']}")
        st.markdown(f"*{current_level['description']}*")
    with col2:
        st.info(f"🏆 解鎖徽章\n\n**{current_level['badge']}**")

    level_id = current_level['id']
    total_rounds = current_level.get("total_rounds", 2)

    # 初始化本關多回合歷程
    if "rpg_chat_history" not in st.session_state:
        st.session_state.rpg_chat_history = {}
    if level_id not in st.session_state.rpg_chat_history:
        st.session_state.rpg_chat_history[level_id] = []

    chat_history = st.session_state.rpg_chat_history[level_id]
    completed_rounds = len(chat_history)
    current_round = completed_rounds + 1
    is_game_finished = (completed_rounds >= total_rounds) or (completed_rounds > 0 and chat_history[-1].get("is_completed", False))

    # 進度指示
    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        if is_game_finished:
            st.success(f"🎉 **【已完勝通關！】** 本關 {total_rounds} 回合攻防戰已全部圓滿達成！")
        else:
            st.info(f"⚔️ **【回合戰況】** 目前進行至：**第 {current_round} / {total_rounds} 回合**（接住對手出招並化解攻勢！）")
    with col_info2:
        pass_ratio = min(1.0, completed_rounds / total_rounds)
        st.progress(pass_ratio)

    # 1. 歷史對話歷程呈現（對話氣泡流）
    if chat_history:
        st.markdown("### 📜 兩人的交鋒對話紀錄")
        for item in chat_history:
            r_num = item["round"]
            eval_data = item.get("eval_data", {})
            st.markdown(f"#### 🚩 第 {r_num} 回合交鋒")
            
            # 對手台詞
            st.markdown(f"""
            <div class="npc-box">
                <b>{current_level['npc_avatar']} {current_level['npc_name']}：</b><br>
                <span style="font-size: 1.05rem;">{item['npc_speech']}</span>
            </div>
            """, unsafe_allow_html=True)

            # 美女貓貓回覆
            st.markdown(f"""
            <div style="background-color: #f1f2f6; border-left: 5px solid #2ed573; padding: 0.9rem; border-radius: 8px; margin: 0.8rem 0;">
                <b>👑 美女貓貓的回答：</b><br>
                <span style="font-size: 1.05rem; color: #2f3542;">{item['user_reply']}</span>
            </div>
            """, unsafe_allow_html=True)

            # mia 貓講評展開或直接顯示
            with st.expander(f"🔍 查看第 {r_num} 回合評鑑成績單（得分：{eval_data.get('overall_score', 85)} 分）", expanded=(r_num == completed_rounds)):
                # 歷史回合通關錦囊回顧
                hist_hint = item.get("round_hint") or get_round_hint(current_level, r_num, chat_history[:r_num-1])
                st.markdown(f"💡 **第 {r_num} 回合通關錦囊回顧**：\n> *{hist_hint}*")
                st.divider()

                # 來源標記
                if eval_data.get("source") == "real_ai":
                    m_name = eval_data.get("model_used", "Gemini")
                    st.success(f"🟢 **由 Google Gemini 即時分析生成（`{m_name}`）**")
                elif eval_data.get("source") == "mock_fallback":
                    st.warning("🟡 **連線稍有延遲，mia 貓已啟動【守護展示示範模式】**")
                else:
                    st.info("🟡 **當前為【免 Key 智慧模擬示範】**")

                # 成績儀表板
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("💖 同理心", f"{eval_data.get('empathy_score', 80)} 分")
                m2.metric("🎯 清晰度", f"{eval_data.get('clarity_score', 80)} 分")
                m3.metric("✨ 得體度", f"{eval_data.get('tact_score', 80)} 分")
                m4.metric("🏆 綜合得分", f"{eval_data.get('overall_score', 80)} 分")

                st.markdown(f"""
                <div class="mia-feedback">
                    <b>🐾 mia 貓點評：</b> {eval_data.get('encouragement', '')}<br><br>
                    <b>💬 {current_level['npc_name']} 心理反應：</b> {eval_data.get('npc_reaction', '')}
                </div>
                """, unsafe_allow_html=True)

                makeover = eval_data.get("magic_makeover", {})
                if makeover:
                    st.markdown(f"""
                    <div class="magic-box">
                        <b>🪄 mia 貓的「魔法變身」神回覆：</b><br>
                        <span style="color: #10ac84; font-weight: 600;">『{makeover.get('golden_version', '')}』</span><br>
                        <small style="color: #57606f;">💡 為什麼更好：{makeover.get('why_better', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            st.divider()

    # 2. 當前最新回合互動區（若尚未完結）
    if not is_game_finished:
        if completed_rounds == 0:
            current_npc_speech = current_level['scenario']
        else:
            current_npc_speech = chat_history[-1].get("next_npc_speech", "（等待接招...）")

        st.markdown(f"""
        <div class="npc-box" style="border-left-color: #ff4757; background-color: #fff0f3;">
            <h4>{current_level['npc_avatar']} {current_level['npc_name']}（第 {current_round} 回合出招）：</h4>
            <p style="font-size: 1.15rem; font-weight: 500; margin-top: 8px;">
                {current_npc_speech}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 當前回合專屬通關錦囊提示（每回合專屬，卡關時點開）
        current_hint = get_round_hint(current_level, current_round, chat_history)
        with st.expander(f"💡 看看 mia 貓的第 {current_round} 回合通關提示（卡關時再點開喔！）"):
            st.info(f"🐾 **第 {current_round} 回合拆招錦囊：**\n\n{current_hint}")

        # 輸入框 key 綁定重置計數器，重置時保證完全清空
        reset_cnt = st.session_state.get(f"reset_cnt_{level_id}", 0)
        input_key = f"input_{level_id}_round_{current_round}_{reset_cnt}"

        user_reply = st.text_area(
            f"💬 美女貓貓請接招（輸入你想對 {current_level['npc_name']} 說的話）：",
            height=100,
            placeholder="例如：哈哈，被你發現了！最近心情好胃口也跟著好...",
            key=input_key
        )

        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            btn_text = "🚀 送出回覆，繼續接招！" if current_round < total_rounds else "🏆 送出最後一擊，挑戰完勝！"
            submit_reply = st.button(btn_text, type="primary", use_container_width=True, key=f"btn_sub_{level_id}_{current_round}")
        with col_act2:
            if st.button("🧹 徹底重置本關（全清空）", use_container_width=True, key=f"btn_reset_{level_id}"):
                st.session_state.rpg_chat_history[level_id] = []
                st.session_state[f"reset_cnt_{level_id}"] = reset_cnt + 1
                st.rerun()

        if submit_reply:
            if not user_reply.strip():
                st.warning("喵～美女貓貓還沒輸入任何話呢！請先說一句話再來接招喔！🐾")
            else:
                with st.spinner("🐾 mia 貓正在拿放大鏡為妳的回答做 X 光全身透視..."):
                    # 組合歷史對話文本
                    hist_lines = []
                    for h in chat_history:
                        hist_lines.append(f"第 {h['round']} 回合 NPC: {h['npc_speech']}\n美女貓貓: {h['user_reply']}")
                    hist_text = "\n\n".join(hist_lines) if hist_lines else "（這是第一回合開場）"

                    if client:
                        prompt = EQ_MULTI_ROUND_PROMPT.format(
                            level_name=current_level['name'],
                            npc_name=current_level['npc_name'],
                            scenario=current_level['scenario'],
                            round_num=current_round,
                            total_rounds=total_rounds,
                            chat_history=hist_text,
                            current_npc_speech=current_npc_speech,
                            user_response=user_reply
                        )
                        raw_res = call_gemini(client, prompt)
                        try:
                            eval_data = clean_json_response(raw_res)
                            eval_data["source"] = "real_ai"
                            eval_data["model_used"] = st.session_state.get("active_gemini_model", "Gemini")
                        except Exception:
                            # 容錯降級為離線腳本
                            offline_rounds = current_level.get("offline_rounds", [])
                            idx = min(current_round - 1, len(offline_rounds) - 1)
                            eval_data = offline_rounds[idx].get("mock_result", {}).copy()
                            eval_data["source"] = "mock_fallback"
                    else:
                        offline_rounds = current_level.get("offline_rounds", [])
                        idx = min(current_round - 1, len(offline_rounds) - 1)
                        eval_data = offline_rounds[idx].get("mock_result", {}).copy()
                        eval_data["source"] = "mock"

                    # 判斷是否為完結回合
                    is_done = eval_data.get("is_completed", current_round >= total_rounds)
                    next_speech = eval_data.get("next_npc_speech", "（對話圓滿結束）")

                    # 存入對話鏈（含本回合專屬提示）
                    chat_history.append({
                        "round": current_round,
                        "npc_speech": current_npc_speech,
                        "user_reply": user_reply,
                        "round_hint": current_hint,
                        "eval_data": eval_data,
                        "next_npc_speech": next_speech,
                        "is_completed": is_done
                    })
                    st.session_state.rpg_chat_history[level_id] = chat_history
                    st.rerun()

    else:
        # 已完結畫面（通關結算）
        st.balloons()
        avg_score = int(sum(h["eval_data"].get("overall_score", 85) for h in chat_history) / len(chat_history))
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e8f7ee, #d1f2db); border: 2px solid #2ed573; border-radius: 12px; padding: 1.5rem; text-align: center; margin: 1.5rem 0;">
            <h2 style="color: #2ed573; margin-bottom: 0.5rem;">🎉 恭喜美女貓貓完勝通關！</h2>
            <h4 style="color: #2f3542;">🏆 解鎖榮譽徽章：<b>{current_level['badge']}</b></h4>
            <p style="font-size: 1.2rem; color: #57606f; margin-top: 10px;">
                全場 {total_rounds} 回合平均實力得分：<b style="color: #ff4757; font-size: 1.6rem;">{avg_score}</b> 分！
            </p>
            <p style="color: #2f3542;"><b>{current_level['npc_name']}：</b>『{chat_history[-1].get('next_npc_speech', '跟妳聊天真的很愉快！')}』</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🧹 重新再挑戰一次本關（清空重頭來）", type="primary", use_container_width=True, key=f"btn_restart_{level_id}"):
            st.session_state.rpg_chat_history[level_id] = []
            st.session_state[f"reset_cnt_{level_id}"] = st.session_state.get(f"reset_cnt_{level_id}", 0) + 1
            st.rerun()

# ==============================================================================
# 📝 模式二：150字長話短說練功房
# ==============================================================================

else:
    st.markdown('<div class="main-title">📝 150 字「長話短說」練功房</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">長話短說是職場最頂級的保命力！把 500 字的混亂局勢，在 150 字內直切要害！</div>', unsafe_allow_html=True)

    # 初始化 session_state
    if "current_story" not in st.session_state:
        st.session_state.current_story = OFFLINE_STORIES[0]["content"]
        st.session_state.current_title = OFFLINE_STORIES[0]["title"]
    if "summary_user_input" not in st.session_state:
        st.session_state.summary_user_input = ""
    if "summary_eval_res" not in st.session_state:
        st.session_state.summary_eval_res = None
    if "need_random_story" not in st.session_state:
        st.session_state.need_random_story = False

    def on_click_random_story():
        # 標記需要生成新題目，並強制清空作答區與評鑑結果
        st.session_state.need_random_story = True
        st.session_state.summary_user_input = ""
        st.session_state.summary_eval_res = None

    def on_click_clear_summary():
        # 單純清空作答區與評鑑結果
        st.session_state.summary_user_input = ""
        st.session_state.summary_eval_res = None

    # 出題按鈕與操作區（透過 on_click 回呼保證精準清空作答區）
    c_btn1, c_btn2, _ = st.columns([2.5, 2, 3.5])
    with c_btn1:
        st.button("🎲 隨機產生全新題目（AI 出題）", type="secondary", use_container_width=True, on_click=on_click_random_story)

    with c_btn2:
        st.button("🧹 清空答案重寫", type="secondary", use_container_width=True, on_click=on_click_clear_summary)

    # 若觸發隨機出題，在此執行切換題目與載入（提供 spinner 動態反饋）
    if st.session_state.need_random_story:
        st.session_state.need_random_story = False
        with st.spinner("🐾 mia 貓正在為美女貓貓編寫棘手的職場狀況題..."):
            if client:
                new_story = call_gemini(client, SUMMARY_GEN_PROMPT)
                if new_story.strip():
                    st.session_state.current_story = new_story.strip()
                    st.session_state.current_title = "真實職場緊急狀況模擬"
            else:
                # 切換內建題庫（避免抽到重複同一篇）
                import random
                candidates = [s for s in OFFLINE_STORIES if s["content"] != st.session_state.get("current_story")]
                picked = random.choice(candidates if candidates else OFFLINE_STORIES)
                st.session_state.current_story = picked["content"]
                st.session_state.current_title = picked["title"]

    story_text = st.session_state.current_story
    story_len = len(story_text)

    # 題目卡片
    st.markdown(f"""
    <div class="stCard">
        <h4>📋 題目情境：{st.session_state.get('current_title', '職場狀況題')}</h4>
        <p style="color: #747d8c; font-size: 0.9rem;">原文篇幅：約 {story_len} 字（請在 150 字內抓出核心與對策）</p>
        <p style="font-size: 1.05rem; line-height: 1.6; color: #2f3542; margin-top: 10px;">
            {story_text}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 作答區與即時字數計（綁定 summary_user_input 保證換題時自動徹底清空）
    user_summary = st.text_area(
        "✍️ 美女貓貓的精華總結作答區（建議 150 字以內，超標亦可送出評鑑）：",
        height=130,
        placeholder="請抓住重點：發生了什麼事？核心原因是什麼？目前面臨的危機？當前最迫切需要採取的下一步行動？",
        key="summary_user_input"
    )

    current_chars = len(user_summary)
    is_overflow = current_chars > 150

    # 字數警示膠囊
    if current_chars == 0:
        badge_style = "background-color: #f1f2f6; color: #747d8c;"
        badge_text = "尚未輸入字數 (0 / 150 字)"
    elif is_overflow:
        badge_style = "background-color: #ff6b81; color: white;"
        badge_text = f"⚠️ 目前已輸入 {current_chars} / 150 字（超出 {current_chars - 150} 字，但別擔心！依舊能使用評鑑，mia 貓會幫妳抓贅字與指導如何修剪喔！🐾）"
    else:
        badge_style = "background-color: #2ed573; color: white;"
        badge_text = f"✅ 字數標準！目前已輸入 {current_chars} / 150 字（還能寫 {150 - current_chars} 字）"

    st.markdown(f'<span class="counter-badge" style="{badge_style}">{badge_text}</span>', unsafe_allow_html=True)

    # 💡 輸入下方的長話短說指導原則卡片（直覺生活化，小學生也能懂的 150 字骨架指南）
    st.markdown("""
    <div class="stCard" style="background: linear-gradient(135deg, #fffdfa 0%, #ffffff 100%); border-left: 5px solid #ff9f43; margin: 12px 0 16px 0; padding: 1rem 1.2rem;">
        <h4 style="margin: 0 0 8px 0; color: #e67e22; font-size: 1.1rem; display: flex; align-items: center; gap: 6px;">
            💡 mia 貓的長話短說「保命三大心法」（150 字黃金骨架指南）：
        </h4>
        <div style="font-size: 0.95rem; line-height: 1.7; color: #2f3542;">
            <p style="margin: 4px 0;"><b>1️⃣ 結論先行（火燒眉毛先講）：</b> 直接說「發生了什麼重大後果與危機」（例如：系統中斷，每分鐘損失數十萬）。不從盤古開天開場！</p>
            <p style="margin: 4px 0;"><b>2️⃣ 一句話直擊死結（講卡關原因）：</b> 點出當前最核心的卡關瓶頸（例如：備援切換需休假架構師授權）。不扯無關八卦與抱怨！</p>
            <p style="margin: 4px 0;"><b>3️⃣ 眼下最迫切的第一步（講當前行動）：</b> 說出最需要主管裁決或團隊立刻執行的下一步（例如：先取得緊急授權切換止血，會後再行究責）。</p>
            <hr style="border: 0; border-top: 1px dashed #ffa502; margin: 8px 0;">
            <p style="color: #d35400; font-size: 0.9rem; margin: 4px 0 0 0;">
                🐾 <b>mia 貓修剪小秘訣（贅字大掃除）：</b> 刪掉「基本上來說」、「我覺得可能」、「大家都知道」等心情描寫與空泛修飾，只留<b>【事實 ＋ 關鍵數據 ＋ 對策行動】</b>，哪怕字數超標也能神速修回 150 字！
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 提交總結，進行長話短說評鑑！", type="primary"):
        if not user_summary.strip():
            st.warning("喵～請先寫下妳的精華總結再送出喔！🐾")
        else:
            with st.spinner("🐾 mia 貓裁判正在逐字檢查重點捕捉率與精煉度..."):
                if client:
                    prompt = SUMMARY_EVAL_PROMPT.format(
                        original_story=story_text,
                        original_length=story_len,
                        user_summary=user_summary,
                        summary_length=current_chars
                    )
                    raw_res = call_gemini(client, prompt)
                    try:
                        eval_res = clean_json_response(raw_res)
                        eval_res["source"] = "real_ai"
                        eval_res["model_used"] = st.session_state.get("active_gemini_model", "Gemini")
                    except Exception:
                        is_ok = current_chars <= 150
                        eval_res = {
                            "source": "mock_fallback",
                            "actual_char_count": current_chars,
                            "is_under_150": is_ok,
                            "core_focus_score": 90 if is_ok else 82,
                            "conciseness_score": 88 if is_ok else 75,
                            "overall_score": 89 if is_ok else 78,
                            "evaluation_feedback": f"美女貓貓的總結非常有條理！清楚點出了核心起因與危機。{'字數完全合規，很棒！' if is_ok else f'雖然目前寫了 {current_chars} 字（超出 150 字），但核心重點抓得很好！不用擔心，只要參考下方 mia 貓幫妳挑出的贅字並修剪掉，就能輕鬆壓縮進 150 字囉！'}",
                            "wordy_phrases_found": ["例如『基本上來說』可以刪掉", "『大家都覺得很著急』可精簡為『情況急迫』", "冗長的情緒與背景可簡化為一句話"],
                            "perfect_150_demo": "雙十一暖身慶因雲端網路中斷導致結帳當機，每分鐘損失數十萬，總經理限期一小時修復。當前瓶頸為備援伺服器切換需休假架構師授權，各部門各執一詞。首要對策應立即取得緊急授權切換系統止血，並統一對外公關口徑，會後再行究責。（122字）",
                            "secret_tip": "長話短說金字塔心法：① 先講火燒眉毛的結果 ② 再講卡關的單一原因 ③ 最後講眼下最該做的第一步！"
                        }
                else:
                    # 離線評審範例（字數超標依然能順暢體驗完整評估與指導）
                    is_ok = current_chars <= 150
                    eval_res = {
                        "source": "mock",
                        "actual_char_count": current_chars,
                        "is_under_150": is_ok,
                        "core_focus_score": 92 if is_ok else 82,
                        "conciseness_score": 88 if is_ok else 75,
                        "overall_score": 90 if is_ok else 78,
                        "evaluation_feedback": f"美女貓貓的總結非常有條理！清楚點出了核心起因與目前的危機。{'字數完全合規，太厲害了！' if is_ok else f'雖然目前寫了 {current_chars} 字（稍超出 150 字標準），但核心重點抓得很好！不用擔心，只要參考下方 mia 貓幫妳挑出的贅字並修剪掉，就能輕鬆壓縮進 150 字囉！'}",
                        "wordy_phrases_found": ["例如『基本上來說』可以刪掉", "『大家都覺得很著急』可精簡為『情況急迫』", "冗長的角色情緒描寫可以大幅濃縮"],
                        "perfect_150_demo": "雙十一暖身慶因雲端網路中斷導致結帳當機，每分鐘損失數十萬，總經理限期一小時修復。當前瓶頸為備援伺服器切換需休假架構師授權，各部門各執一詞。首要對策應立即取得緊急授權切換系統止血，並統一對外公關口徑，會後再行究責。（122字）",
                        "secret_tip": "長話短說金字塔心法：① 先講火燒眉毛的結果 ② 再講卡關的單一原因 ③ 最後講眼下最該做的第一步！"
                    }
                st.session_state.summary_eval_res = eval_res

    # 展示評鑑結果（若存在）
    eval_res = st.session_state.get("summary_eval_res")
    if eval_res:
        st.success("🎉 評鑑出爐！")
        source = eval_res.get("source")
        if source == "real_ai":
            m_used = eval_res.get("model_used", "Gemini")
            st.success(f"🟢 **此評鑑由 Google Gemini 即時分析生成！（驅動大腦：`{m_used}`）**")
        elif source == "mock_fallback":
            st.warning("🟡 **剛才連線 Google Gemini 遇到微小阻礙，mia 貓已為您啟動【守護展示示範模式】，確保畫面順暢！**")
        else:
            st.info("🟡 **當前為【免 Key 智慧模擬示範】（填入 Gemini API Key 即可啟動真實 AI 即時評分！）**")

        # 成績評分
        s1, s2, s3, s4 = st.columns(4)
        is_under = eval_res.get("is_under_150", False)
        s1.metric("📏 150 字檢驗", "合格 ✅" if is_under else "超標 ⚠️（可修剪）", f"{eval_res.get('actual_char_count', current_chars)} 字")
        s2.metric("🎯 重點捕捉率", f"{eval_res.get('core_focus_score', 85)} 分")
        s3.metric("✂️ 精煉程度", f"{eval_res.get('conciseness_score', 85)} 分")
        s4.metric("🏆 綜合實力分", f"{eval_res.get('overall_score', 85)} 分")

        # mia 貓講評
        st.markdown(f"""
        <div class="mia-feedback">
            <h4>🐾 mia 貓的教練總評：</h4>
            <p>{eval_res.get('evaluation_feedback', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        # 贅詞抓漏
        wordy = eval_res.get("wordy_phrases_found", [])
        if wordy:
            with st.expander("✂️ mia 貓幫妳抓出可以再精簡的小贅字：", expanded=True if is_overflow else False):
                for item in wordy:
                    st.write(f"- {item}")

        # 滿分示範與小祕技
        st.markdown(f"""
        <div class="magic-box">
            <h4>🌟 mia 貓示範的滿分 150 字神總結：</h4>
            <p style="font-size: 1.1rem; line-height: 1.6; color: #10ac84;">
                『{eval_res.get('perfect_150_demo', '')}』
            </p>
            <hr style="border: 0; border-top: 1px dashed #2ed573; margin: 10px 0;">
            <p><b>💡 長話短說必勝口訣：</b> {eval_res.get('secret_tip', '')}</p>
        </div>
        """, unsafe_allow_html=True)
