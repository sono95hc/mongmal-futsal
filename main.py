import streamlit as st
import random
import pandas as pd
import json
import os
import itertools
from datetime import datetime, timedelta
import urllib.request
import urllib.error
import base64

st.set_page_config(page_title="몽말 팀배분 프로그램 by홍찬", layout="centered")

DB_FILE = "futsal_data.json"

def safe_float(val, default=3.0):
    try:
        return round(float(val), 2)
    except:
        return default

def safe_int(val, default=1000):
    try:
        return int(float(val))
    except:
        return default

def push_to_github(content_str):
    try:
        if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
            return
            
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
        path = "futsal_data.json"
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "Streamlit-Auto-Backup"
        }
        
        req_get = urllib.request.Request(url, headers=headers)
        sha = ""
        try:
            with urllib.request.urlopen(req_get) as response:
                res_data = json.loads(response.read().decode())
                sha = res_data.get("sha", "")
        except urllib.error.URLError:
            pass 
            
        encoded_content = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
        payload = {
            "message": "Auto-update futsal_data.json via Streamlit",
            "content": encoded_content
        }
        if sha:
            payload["sha"] = sha
            
        req_put = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='PUT')
        with urllib.request.urlopen(req_put) as response:
            pass
    except Exception:
        pass

def get_blank_score_df(mode="3파전"):
    if "2파전" in mode:
        quarters = [f"{i}쿼터" for i in range(1, 9)]
        return pd.DataFrame({"블루": [None] * 8, "레드": [None] * 8}, index=quarters)
    else:
        quarters = [f"{i}쿼터" for i in range(1, 10)]
        return pd.DataFrame({"블루": [None] * 9, "블랙": [None] * 9, "레드": [None] * 9}, index=quarters)

def load_permanent_data():
    default_data = {
        "MEMBER_DATABASE": {
            "손흥민": {"공격": 5.0, "수비": 4.0, "키퍼": 2.0, "MMR": 1000},
            "이강인": {"공격": 5.0, "수비": 3.0, "키퍼": 2.0, "MMR": 1000},
            "황희찬": {"공격": 4.0, "수비": 3.0, "키퍼": 1.0, "MMR": 1000},
            "김민재": {"공격": 2.0, "수비": 5.0, "키퍼": 3.0, "MMR": 1000},
            "조현우": {"공격": 1.0, "수비": 2.0, "키퍼": 5.0, "MMR": 1000}
        },
        "attendance_list": ["손흥민", "이강인", "황희찬", "김민재", "조현우"],
        "late_list": [],
        "match_mode": "3파전",
        "score_data_dict": get_blank_score_df("3파전").to_dict(orient="list"),
        "history_logs": [],
        "current_teams": {},
        "current_q_idx": 0,
        "settlement_katalk_text": ""
    }

    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                if "MEMBER_DATABASE" not in data: data["MEMBER_DATABASE"] = default_data["MEMBER_DATABASE"]
                
                for p_name in data["MEMBER_DATABASE"]:
                    if "MMR" not in data["MEMBER_DATABASE"][p_name]:
                        data["MEMBER_DATABASE"][p_name]["MMR"] = 1000
                        
                if "attendance_list" not in data: data["attendance_list"] = default_data["attendance_list"]
                if "late_list" not in data: data["late_list"] = default_data["late_list"]
                if "match_mode" not in data: data["match_mode"] = "3파전"
                if "score_data_dict" not in data: data["score_data_dict"] = default_data["score_data_dict"]
                if "history_logs" not in data: data["history_logs"] = []
                if "current_teams" not in data: data["current_teams"] = {}
                if "current_q_idx" not in data: data["current_q_idx"] = 0
                if "settlement_katalk_text" not in data: data["settlement_katalk_text"] = ""
                    
                if "경기팀" in data["score_data_dict"]:
                    del data["score_data_dict"]["경기팀"]
                    
                return data
        except:
            pass
            
    return default_data

def save_permanent_data():
    try:
        score_dict = st.session_state.edited_score_df.to_dict(orient="list")
    except:
        score_dict = get_blank_score_df(st.session_state.get("match_mode", "3파전")).to_dict(orient="list")

    att_list = st.session_state.get("attendance_list", [])
    clean_attendance = [str(x).strip() for x in att_list if x and str(x).strip()]
    
    late_list = st.session_state.get("late_list", [])
    clean_late = [str(x).strip() for x in late_list if x and str(x).strip()]
    
    data_to_save = {
        "MEMBER_DATABASE": st.session_state.get("MEMBER_DATABASE", {}),
        "attendance_list": clean_attendance,
        "late_list": clean_late,
        "match_mode": st.session_state.get("match_mode", "3파전"),
        "score_data_dict": score_dict,
        "history_logs": st.session_state.get("history_logs", []),
        "current_teams": st.session_state.get("current_teams", {}),
        "current_q_idx": st.session_state.get("current_q_idx", 0),
        "settlement_katalk_text": st.session_state.get("settlement_katalk_text", "")
    }
    
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            
        json_str = json.dumps(data_to_save, ensure_ascii=False, indent=4)
        push_to_github(json_str)
    except:
        pass

perm_data = load_permanent_data()

if "MEMBER_DATABASE" not in st.session_state: st.session_state.MEMBER_DATABASE = perm_data.get("MEMBER_DATABASE", {})
if "attendance_list" not in st.session_state: st.session_state.attendance_list = [str(x).strip() for x in perm_data.get("attendance_list", []) if x and str(x).strip()]
if "late_list" not in st.session_state: st.session_state.late_list = [str(x).strip() for x in perm_data.get("late_list", []) if x and str(x).strip()]
if "match_mode" not in st.session_state: st.session_state.match_mode = perm_data.get("match_mode", "3파전")
if "history_logs" not in st.session_state: st.session_state.history_logs = perm_data.get("history_logs", [])
if "current_teams" not in st.session_state: st.session_state.current_teams = perm_data.get("current_teams", {})
if "current_q_idx" not in st.session_state: st.session_state.current_q_idx = perm_data.get("current_q_idx", 0)
if "settlement_katalk_text" not in st.session_state: st.session_state.settlement_katalk_text = perm_data.get("settlement_katalk_text", "")
if "ai_teams" not in st.session_state: st.session_state.ai_teams = {}

if "edited_score_df" not in st.session_state:
    mode = st.session_state.match_mode
    saved_dict = perm_data.get("score_data_dict", {})
    try:
        if saved_dict and isinstance(saved_dict, dict) and len(list(saved_dict.values())[0]) > 0:
            dict_len = len(list(saved_dict.values())[0])
            quarters = [f"{i}쿼터" for i in range(1, dict_len + 1)]
            st.session_state.edited_score_df = pd.DataFrame(saved_dict, index=quarters)
        else:
            st.session_state.edited_score_df = get_blank_score_df(mode)
    except Exception:
        st.session_state.edited_score_df = get_blank_score_df(mode)

if "temp_match_type" not in st.session_state: st.session_state.temp_match_type = "블루 vs 레드"
if "bulk_input_df" not in st.session_state:
    st.session_state.bulk_input_df = pd.DataFrame({
        "이름": [""] * 15, "공격": [3.0] * 15, "수비": [3.0] * 15, "키퍼": [3.0] * 15, "MMR": [1000] * 15
    })
if "show_warning" not in st.session_state: st.session_state.show_warning = False
if "confirm_close" not in st.session_state: st.session_state.confirm_close = False

def make_podium_html(title, data_list, unit=""):
    while len(data_list) < 3:
        data_list.append(("-", "-"))

    n1, v1 = data_list[0]
    n2, v2 = data_list[1]
    n3, v3 = data_list[2]

    v1_str = f"{v1}{unit}" if str(v1) != "-" else "-"
    v2_str = f"{v2}{unit}" if str(v2) != "-" else "-"
    v3_str = f"{v3}{unit}" if str(v3) != "-" else "-"

    html = f"""
    <div style="text-align: center; margin-bottom: 20px; padding: 15px; border-radius: 10px; background-color: #1E1E1E;">
        <h4 style="color: #FFFFFF; margin-bottom: 20px; font-weight: bold;">{title}</h4>
        <div style="display: flex; justify-content: center; align-items: flex-end; height: 140px; gap: 4px;">
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center;">
                <div style="font-size: 0.9em; font-weight: bold; color: #E0E0E0;">{n2}</div>
                <div style="font-size: 0.7em; color: #A0A0A0; margin-bottom: 4px;">{v2_str}</div>
                <div style="background: linear-gradient(180deg, #BDBDBD 0%, #757575 100%); width: 100%; height: 70px; border-radius: 4px 4px 0 0; display: flex; justify-content: center; align-items: center; font-weight: bold; color: white;">2</div>
            </div>
            <div style="flex: 1.2; display: flex; flex-direction: column; align-items: center;">
                <div style="font-size: 1.1em; font-weight: bold; color: #FFD700;">{n1}</div>
                <div style="font-size: 0.8em; color: #A0A0A0; margin-bottom: 4px;">{v1_str}</div>
                <div style="background: linear-gradient(180deg, #FFD700 0%, #F57F17 100%); width: 100%; height: 100px; border-radius: 4px 4px 0 0; display: flex; justify-content: center; align-items: center; font-size: 1.5em; font-weight: bold; color: white;">1</div>
            </div>
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center;">
                <div style="font-size: 0.85em; font-weight: bold; color: #CD7F32;">{n3}</div>
                <div style="font-size: 0.7em; color: #A0A0A0; margin-bottom: 4px;">{v3_str}</div>
                <div style="background: linear-gradient(180deg, #CD7F32 0%, #8D6E63 100%); width: 100%; height: 45px; border-radius: 4px 4px 0 0; display: flex; justify-content: center; align-items: center; font-weight: bold; color: white;">3</div>
            </div>
        </div>
    </div>
    """
    return html

menu_1 = "1. 명단 및 팀배분"
menu_2 = "2. 경기 기록실"
menu_3 = "3. 날짜별 기록실"
menu_4 = "4. 회원별 통계실"
menu_5 = "5. 회원별 점수"

st.sidebar.title("MENU")
st.sidebar.markdown("---")
st.sidebar.subheader("관리자 인증")

try:
    admin_secret_pw = st.secrets["ADMIN_PW"]
except:
    admin_secret_pw = "0330"

admin_password = st.sidebar.text_input("비밀번호 입력", type="password")
is_admin = (admin_password == admin_secret_pw) if admin_password else False

if is_admin:
    menu_options = [menu_1, menu_2, menu_3, menu_4, menu_5]
else:
    menu_options = [menu_1, menu_2, menu_3, menu_4]

page = st.sidebar.radio("메뉴를 선택하세요", menu_options)
st.sidebar.caption("제작자: by홍찬")

# =========================================================================
# 1페이지
# =========================================================================
if page == menu_1:
    st.title("몽말 팀배분 프로그램")
    
    st.subheader("[1단계] 참석자 및 추가 인원 입력")
    
    current_att_str = " ".join([x for x in st.session_state.attendance_list if x])
    att_input = st.text_area("최초 참석자 명단 (AI 밸런스 자동 매칭용)", value=current_att_str, height=80)
    
    current_late_str = " ".join([x for x in st.session_state.late_list if x])
    late_input = st.text_area("추가 인원 명단 (블랙 -> 레드 -> 블루 순차 배정용)", value=current_late_str, height=60, placeholder="지각생 등 추가 참석자 입력")
    
    raw_att_list = [x.strip() for x in att_input.split() if x.strip()]
    current_att_list = []
    for x in raw_att_list:
        if x not in current_att_list:
            current_att_list.append(x)
            
    raw_late_list = [x.strip() for x in late_input.split() if x.strip()]
    current_late_list = []
    for x in raw_late_list:
        if x not in current_att_list and x not in current_late_list:
            current_late_list.append(x)
            
    if current_att_list != st.session_state.attendance_list or current_late_list != st.session_state.late_list:
        st.session_state.attendance_list = current_att_list
        st.session_state.late_list = current_late_list
        save_permanent_data()
        
    total_att_list = current_att_list + current_late_list
        
    st.markdown("---")
    st.subheader("[2단계] 경기 방식 설정")
    selected_mode = st.radio("오늘 매치 방식을 골라주세요", ["2파전 (8쿼터)", "3파전 (9쿼터)"], index=0 if "2파전" in st.session_state.match_mode else 1)
    team_options = ["미배정", "레드", "블루"] if "2파전" in selected_mode else ["미배정", "블랙", "레드", "블루"]

    st.markdown("---")
    st.subheader("[3단계] 팀 편성 (자동+수동 조합)")
    st.write("상황에 맞게 아래 버튼을 선택하여 팀을 배분하세요.")
    st.caption("[안내] 꼼수 방지를 위해 명단이 같으면 기본적으로 같은 결과가 나옵니다. 팀 밸런스가 아쉬워서 다른 팀 배정을 원하시면 아래 '팀 섞기 번호'를 올려주세요.")
    
    match_seed = st.number_input("팀 섞기 번호 (번호를 바꾸면 새로운 팀 조합이 나옵니다)", min_value=1, value=1, step=1)
    
    col_ai1, col_ai2 = st.columns(2)
    
    with col_ai1:
        btn_full_ai = st.button("최초 참석자 AI 매칭 (새로 짜기)", use_container_width=True)
    with col_ai2:
        btn_fill_new = st.button("추가 인원 순차 배정 (블랙>레드>블루)", use_container_width=True)
    
    if btn_full_ai:
        now_kst = datetime.utcnow() + timedelta(hours=9)
        today_date_str = now_kst.strftime("%Y-%m-%d")
        roster_str = "".join(sorted(current_att_list))
        # 날짜 + 명단 + '팀 섞기 번호'를 합쳐서 시드 고정. 번호를 바꾸면 새롭게 리롤 가능!
        random.seed(today_date_str + roster_str + str(match_seed))
        
        prev_teams = {}
        if st.session_state.history_logs:
            last_log = st.session_state.history_logs[-1]
            for p_name, f_info in last_log.get("fines", {}).items():
                prev_teams[p_name] = f_info.get("team")
                
        stats_map = {name: {"MP": 0, "W": 0} for name in st.session_state.MEMBER_DATABASE.keys()}
        for item in st.session_state.history_logs:
            for p_name, f_info in item.get("fines", {}).items():
                if p_name in stats_map:
                    stats_map[p_name]["MP"] += 1
                    if f_info.get("rank") == 1:
                        stats_map[p_name]["W"] += 1
                
        players = []
        for name in current_att_list:
            base_score = 6.0
            mmr_score = 1000
            if name in st.session_state.MEMBER_DATABASE:
                db_info = st.session_state.MEMBER_DATABASE[name]
                base_score = float(db_info.get("공격", 0)) + float(db_info.get("수비", 0))
                mmr_score = int(db_info.get("MMR", 1000))
            
            effective_score = base_score + ((mmr_score - 1000) * 0.05)
            
            if name in stats_map:
                mp = stats_map[name]["MP"]
                w = stats_map[name]["W"]
                if mp >= 10:
                    win_rate = (w / mp) * 100
                    effective_score += (win_rate - 50) * 0.03 
                    
            players.append({"name": name, "total": effective_score})
            
        players.sort(key=lambda x: x['total'], reverse=True)
        teams_keys = ["레드", "블루"] if "2파전" in selected_mode else ["블랙", "레드", "블루"]
        new_teams = {t: [] for t in teams_keys}
        team_sums = {t: 0.0 for t in teams_keys}
        
        for i in range(0, len(players), len(teams_keys)):
            chunk = players[i:i+len(teams_keys)]
            best_perm = None
            min_cost = float('inf')
            
            perms = list(itertools.permutations(teams_keys, len(chunk)))
            random.shuffle(perms)
            
            for perm in perms:
                same_team_penalty = 0
                temp_team_sums = {t: team_sums[t] for t in teams_keys}
                temp_team_counts = {t: len(new_teams[t]) for t in teams_keys}
                
                for p, t in zip(chunk, perm):
                    temp_team_sums[t] += p["total"]
                    temp_team_counts[t] += 1
                    for existing_p in new_teams[t]:
                        m1, m2 = p["name"], existing_p["name"]
                        if m1 in prev_teams and m2 in prev_teams and prev_teams[m1] == prev_teams[m2]:
                            same_team_penalty += 20.0
                            
                # 6대6 기준 실제 필드 전투력 (평균 점수 * 6)으로 환산하여 분산 계산
                temp_team_expected = {}
                for t in teams_keys:
                    if temp_team_counts[t] > 0:
                        temp_team_expected[t] = (temp_team_sums[t] / temp_team_counts[t]) * 6
                    else:
                        temp_team_expected[t] = 0
                        
                avg_expected = sum(temp_team_expected.values()) / len(teams_keys)
                variance = sum((s - avg_expected)**2 for s in temp_team_expected.values())
                
                cost = same_team_penalty + variance
                if cost < min_cost:
                    min_cost = cost
                    best_perm = perm
                    
            for p, t in zip(chunk, best_perm):
                new_teams[t].append(p)
                team_sums[t] += p["total"]
                
        assigned_dict = {}
        for t_name, members in new_teams.items():
            for p in members:
                assigned_dict[p["name"]] = t_name
                
        st.session_state.ai_teams = assigned_dict
        for p_name, t_name in assigned_dict.items():
            st.session_state[f"sel_{p_name}"] = t_name
            
        random.seed()
        st.rerun()

    if btn_fill_new:
        fill_order = ["블랙", "레드", "블루"] if "3파전" in selected_mode else ["레드", "블루"]
        
        for idx, p in enumerate(current_late_list):
            target_team = fill_order[idx % len(fill_order)]
            st.session_state.ai_teams[p] = target_team
            st.session_state[f"sel_{p}"] = target_team
            
        st.rerun()

    final_team_selections = {}
    if total_att_list:
        cols = st.columns(2)
        for idx, player_name in enumerate(total_att_list):
            col = cols[idx % 2]
            
            default_team = st.session_state.ai_teams.get(player_name, "미배정")
            if default_team not in team_options:
                default_team = "미배정"
            
            with col:
                if f"sel_{player_name}" in st.session_state:
                    if st.session_state[f"sel_{player_name}"] not in team_options:
                        st.session_state[f"sel_{player_name}"] = "미배정"
                else:
                    st.session_state[f"sel_{player_name}"] = default_team
                    
                final_team_selections[player_name] = st.selectbox(
                    f"{player_name}", 
                    options=team_options, 
                    key=f"sel_{player_name}"
                )

    st.markdown("---")
    if st.button("이 편성표대로 팀 확정하기 (점수판 초기화)", use_container_width=True, type="primary"):
        st.session_state.show_warning = True

    if st.session_state.show_warning:
        st.warning("[주의] 팀을 새로 확정하면 현재 경기 기록실의 점수가 모두 초기화됩니다. 진행하시겠습니까?")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("네, 확정합니다", use_container_width=True):
                st.session_state.show_warning = False
                new_mode = "2파전" if "2파전" in selected_mode else "3파전"
                st.session_state.match_mode = new_mode
                
                st.session_state.current_teams = {t: [] for t in team_options if t != "미배정"}
                for p_name, t_name in final_team_selections.items():
                    if t_name != "미배정":
                        st.session_state.current_teams[t_name].append({"name": p_name})
                        
                st.session_state.edited_score_df = get_blank_score_df(new_mode)
                st.session_state.current_q_idx = 0
                st.session_state.settlement_katalk_text = "" 
                
                save_permanent_data()
                st.rerun()
                
        with c2:
            if st.button("아니오, 취소", use_container_width=True):
                st.session_state.show_warning = False
                st.rerun()

    if st.session_state.current_teams and not st.session_state.show_warning:
        st.success("[알림] 매칭이 성공적으로 확정되었습니다.")
        
        katalk_text = f"[풋살 팀 매칭 결과 ({st.session_state.match_mode})]\n"
        for t_name, members in st.session_state.current_teams.items():
            if not members:
                continue
            m_names = [p['name'] for p in members]
            random.shuffle(m_names) 
            katalk_text += f"\n[{t_name}팀] ({len(members)}명)\n{', '.join(m_names)}\n"
            
        st.text_area("[복사 후 카톡 공지용 텍스트]", value=katalk_text, height=140)


# =========================================================================
# 2페이지
# =========================================================================
elif page == menu_2:
    st.title(f"실시간 경기 기록실 ({st.session_state.match_mode})")
    
    st.subheader("쿼터 스코어 입력창")
    st.write("저장 시 자동으로 다음 쿼터로 넘어가며, 언제든 박스를 눌러 이전 쿼터를 수정할 수 있습니다.")
    
    loop_count = 8 if "2파전" in st.session_state.match_mode else 9
    
    if len(st.session_state.edited_score_df) != loop_count:
        st.session_state.edited_score_df = get_blank_score_df(st.session_state.match_mode)
        st.session_state.current_q_idx = 0
        
    quarter_options = [f"{i}쿼터" for i in range(1, loop_count + 1)]
    
    if st.session_state.current_q_idx >= loop_count:
        st.session_state.current_q_idx = 0
        
    selected_q = st.selectbox("기록할 쿼터 선택", quarter_options, index=st.session_state.current_q_idx)
    st.session_state.current_q_idx = quarter_options.index(selected_q)
    
    current_q_data = st.session_state.edited_score_df.loc[selected_q]
    
    val_blue = None
    val_black = None
    val_red = None
    
    if "3파전" in st.session_state.match_mode:
        st.write("이번 쿼터 경기팀 선택하기")
        btn_cols = st.columns(3)
        with btn_cols[0]:
            if st.button("블루 vs 레드", use_container_width=True): st.session_state.temp_match_type = "블루 vs 레드"
        with btn_cols[1]:
            if st.button("블루 vs 블랙", use_container_width=True): st.session_state.temp_match_type = "블루 vs 블랙"
        with btn_cols[2]:
            if st.button("블랙 vs 레드", use_container_width=True): st.session_state.temp_match_type = "블랙 vs 레드"
            
        match_type = st.session_state.temp_match_type
        st.info(f"현재 입력 대기 중인 매치: [{match_type}]")
        
        c1, c2 = st.columns(2)
        if match_type == "블루 vs 레드":
            with c1: val_blue = st.number_input("블루 점수", min_value=0, max_value=99, value=int(current_q_data["블루"]) if pd.notna(current_q_data.get("블루")) else 0, step=1)
            with c2: val_red = st.number_input("레드 점수", min_value=0, max_value=99, value=int(current_q_data["레드"]) if pd.notna(current_q_data.get("레드")) else 0, step=1)
            val_black = None
        elif match_type == "블루 vs 블랙":
            with c1: val_blue = st.number_input("블루 점수", min_value=0, max_value=99, value=int(current_q_data["블루"]) if pd.notna(current_q_data.get("블루")) else 0, step=1)
            with c2: val_black = st.number_input("블랙 점수", min_value=0, max_value=99, value=int(current_q_data["블랙"]) if pd.notna(current_q_data.get("블랙")) else 0, step=1)
            val_red = None
        else:
            with c1: val_black = st.number_input("블랙 점수", min_value=0, max_value=99, value=int(current_q_data["블랙"]) if pd.notna(current_q_data.get("블랙")) else 0, step=1)
            with c2: val_red = st.number_input("레드 점수", min_value=0, max_value=99, value=int(current_q_data["레드"]) if pd.notna(current_q_data.get("레드")) else 0, step=1)
            val_blue = None
            
    else:
        c1, c2 = st.columns(2)
        with c1: val_blue = st.number_input("블루 점수", min_value=0, max_value=99, value=int(current_q_data["블루"]) if pd.notna(current_q_data.get("블루")) else 0, step=1)
        with c2: val_red = st.number_input("레드 점수", min_value=0, max_value=99, value=int(current_q_data["레드"]) if pd.notna(current_q_data.get("레드")) else 0, step=1)

    if st.button("해당 쿼터 점수 저장하기", use_container_width=True, type="primary"):
        st.session_state.edited_score_df.at[selected_q, "블루"] = val_blue
        st.session_state.edited_score_df.at[selected_q, "레드"] = val_red
        if "3파전" in st.session_state.match_mode:
            st.session_state.edited_score_df.at[selected_q, "블랙"] = val_black
            
        if st.session_state.current_q_idx < loop_count - 1:
            st.session_state.current_q_idx += 1
            
        save_permanent_data()
        st.success(f"[{selected_q}] 점수가 성공적으로 저장되었습니다.")
        st.rerun()

    st.markdown("---")
    st.subheader("현재까지 기록된 쿼터 현황판")
    
    display_score_df = st.session_state.edited_score_df.copy()
    display_score_df = display_score_df.fillna("-")
    
    if "PK승" in display_score_df.columns:
        display_score_df = display_score_df.drop(columns=["PK승"])
        
    st.dataframe(display_score_df, use_container_width=True)

    history_keys = ["레드", "블루"] if "2파전" in st.session_state.match_mode else ["레드", "블랙", "블루"]
    history = {t: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS": 0, "MP": 0} for t in history_keys}

    for i in range(loop_count):
        row_data = st.session_state.edited_score_df.iloc[i]
        b_val = row_data.get("블루")
        r_val = row_data.get("레드")
        bl_val = row_data.get("블랙") if "3파전" in st.session_state.match_mode else None
        
        valid_teams = []
        valid_scores = []
        
        if pd.notna(b_val) and str(b_val).strip() != "-": valid_teams.append("블루"); valid_scores.append(int(b_val))
        if pd.notna(r_val) and str(r_val).strip() != "-": valid_teams.append("레드"); valid_scores.append(int(r_val))
        if bl_val is not None and pd.notna(bl_val) and str(bl_val).strip() != "-": valid_teams.append("블랙"); valid_scores.append(int(bl_val))
        
        if len(valid_teams) == 2:
            tm1, tm2 = valid_teams[0], valid_teams[1]
            sc1, sc2 = valid_scores[0], valid_scores[1]
            
            history[tm1]["MP"] += 1; history[tm2]["MP"] += 1
            history[tm1]["GF"] += sc1; history[tm1]["GA"] += sc2
            history[tm2]["GF"] += sc2; history[tm2]["GA"] += sc1
            
            if sc1 > sc2:
                history[tm1]["W"] += 1; history[tm1]["PTS"] += 3; history[tm2]["L"] += 1
            elif sc1 < sc2:
                history[tm2]["W"] += 1; history[tm2]["PTS"] += 3; history[tm1]["L"] += 1
            else:
                history[tm1]["D"] += 1; history[tm1]["PTS"] += 1
                history[tm2]["D"] += 1; history[tm2]["PTS"] += 1

    for t in history:
        history[t]["GD"] = history[t]["GF"] - history[t]["GA"]

    st.subheader("오늘 경기 실시간 순위표")
    sort_df = pd.DataFrame([{"팀": t, "PTS": history[t]["PTS"], "GD": history[t]["GD"], "GF": history[t]["GF"]} for t in history_keys])
    sort_df = sort_df.sort_values(by=["PTS", "GD", "GF"], ascending=[False, False, False]).reset_index(drop=True)

    final_display = []
    for idx, row in sort_df.iterrows():
        t_name = row["팀"]; stat = history[t_name]
        final_display.append({
            "순위": f"{idx+1}위", "팀명": f"{t_name}팀", "경기수": f"{stat['MP']}전",
            "승 - 무 - 패": f"{stat['W']}승 - {stat['D']}무 - {stat['L']}패",
            "승점": f"{stat['PTS']}점", "득실차 (득/실)": f"{stat['GD']} ({stat['GF']}/{stat['GA']})"
        })
    st.table(pd.DataFrame(final_display).set_index("순위"))
    
    st.markdown("---")
    st.subheader("[최종 순위 수동 조정] (승점 동률 / 승부차기용)")
    st.write("승점과 득실차가 같아 승부차기를 진행했다면, 아래 체크박스를 눌러 최종 순위를 직접 지정하세요.")
    
    adjust_rank = st.checkbox("승부차기 결과로 최종 순위 변경하기")
    
    final_ranked_teams = sort_df["팀"].tolist()
    
    if adjust_rank:
        if "3파전" in st.session_state.match_mode:
            c1, c2, c3 = st.columns(3)
            with c1: rank1 = st.selectbox("[ 1위 팀 ]", history_keys, index=history_keys.index(final_ranked_teams[0]))
            with c2: rank2 = st.selectbox("[ 2위 팀 ]", history_keys, index=history_keys.index(final_ranked_teams[1]))
            with c3: rank3 = st.selectbox("[ 3위 팀 ]", history_keys, index=history_keys.index(final_ranked_teams[2]))
            final_ranked_teams = [rank1, rank2, rank3]
        else:
            c1, c2 = st.columns(2)
            with c1: rank1 = st.selectbox("[ 1위 팀 ]", history_keys, index=history_keys.index(final_ranked_teams[0]))
            with c2: rank2 = st.selectbox("[ 2위 팀 ]", history_keys, index=history_keys.index(final_ranked_teams[1]))
            final_ranked_teams = [rank1, rank2]
            
        st.info(f"[안내] 정산 시 반영될 최종 순위: 1위({final_ranked_teams[0]}) / 2위({final_ranked_teams[1]})" + (f" / 3위({final_ranked_teams[2]})" if "3파전" in st.session_state.match_mode else ""))

    if st.session_state.settlement_katalk_text:
        st.success("[알림] 오늘 매치 정산 공지가 완료되었습니다.")
        st.text_area("[복사 후 카톡 공지용 정산 텍스트]", value=st.session_state.settlement_katalk_text, height=160)

    if st.session_state.current_teams:
        st.markdown("---")
        st.subheader("오늘의 정산 마감 구역")
        st.write("경기가 끝났다면 아래 버튼을 눌러 승패에 따른 MMR과 벌금을 확정 지으세요.")
        
        if st.button("오늘 경기 정산 및 마감하기", use_container_width=True, type="primary"):
            st.session_state.confirm_close = True
            
        if st.session_state.confirm_close:
            st.warning("[확인] 정말 오늘 경기를 마감하시겠습니까? (마감 시 승패에 따라 MMR 전투력이 변동됩니다)")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("네, 마감합니다", use_container_width=True):
                    now_utc = datetime.utcnow()
                    now_kst = now_utc + timedelta(hours=9)
                    today_str = now_kst.strftime("%Y-%m-%d %H:%M")
                    
                    log_entry = {
                        "date": today_str,
                        "mode": st.session_state.match_mode,
                        "ranks": {},
                        "fines": {}
                    }
                    
                    for rank_idx, t_name in enumerate(final_ranked_teams):
                        rank_num = rank_idx + 1
                        team_players = [p["name"] for p in st.session_state.current_teams.get(t_name, [])]
                        log_entry["ranks"][f"{rank_num}위"] = f"{t_name}팀 ({', '.join(team_players)})"
                        
                        if "2파전" in st.session_state.match_mode:
                            fine_amount = 0 if rank_num == 1 else 2000
                            mmr_change = 20 if rank_num == 1 else -20
                        else:
                            if rank_num == 1: fine_amount = 0; mmr_change = 20
                            elif rank_num == 2: fine_amount = 1000; mmr_change = 0
                            else: fine_amount = 2000; mmr_change = -20
                            
                        for p_name in team_players:
                            log_entry["fines"][p_name] = {"team": t_name, "rank": rank_num, "fine": fine_amount, "mmr_change": mmr_change}
                            
                            if p_name in st.session_state.MEMBER_DATABASE:
                                current_mmr = int(st.session_state.MEMBER_DATABASE[p_name].get("MMR", 1000))
                                st.session_state.MEMBER_DATABASE[p_name]["MMR"] = current_mmr + mmr_change
                    
                    notice_lines = [f"[몽말 풋살 회비 정산 공지 ({st.session_state.match_mode})]\n"]
                    
                    if "3파전" in st.session_state.match_mode:
                        t2_name = final_ranked_teams[1]
                        t2_players = [p["name"] for p in st.session_state.current_teams.get(t2_name, [])]
                        t3_name = final_ranked_teams[2]
                        t3_players = [p["name"] for p in st.session_state.current_teams.get(t3_name, [])]
                        
                        if t2_players:
                            notice_lines.append(f"[오늘 2등] {t2_name}팀: {', '.join(t2_players)} -> 각 1,000원")
                        if t3_players:
                            notice_lines.append(f"[오늘 3등] {t3_name}팀: {', '.join(t3_players)} -> 각 2,000원")
                    else:
                        t2_name = final_ranked_teams[1]
                        t2_players = [p["name"] for p in st.session_state.current_teams.get(t2_name, [])]
                        if t2_players:
                            notice_lines.append(f"[오늘 2등] {t2_name}팀: {', '.join(t2_players)} -> 각 2,000원")
                            
                    notice_lines.append("\n위 명단에 해당하시는 분들은 아래 계좌로 입금 부탁드립니다.")
                    notice_lines.append("[계좌번호] 카카오뱅크 79421977437 최홍찬")
                    
                    st.session_state.settlement_katalk_text = "\n".join(notice_lines)
                    
                    st.session_state.history_logs.append(log_entry)
                    save_permanent_data()
                    st.session_state.confirm_close = False
                    st.success("[알림] 정산 완료. 승률 및 MMR이 장부에 안전하게 기록되었습니다.")
                    st.rerun()
            with c2:
                if st.button("아니오, 취소", use_container_width=True):
                    st.session_state.confirm_close = False
                    st.rerun()
    
    if is_admin:
        st.markdown("---")
        if st.button("오늘 경기 스코어판 전체 초기화 (관리자 전용)", use_container_width=True):
            st.session_state.edited_score_df = get_blank_score_df(st.session_state.match_mode)
            st.session_state.current_q_idx = 0
            save_permanent_data()
            st.rerun()

# =========================================================================
# 3페이지
# =========================================================================
elif page == menu_3:
    st.title("3. 날짜별 기록실")
    st.write("매주 마감된 경기 결과와 개인별 회비 및 MMR 변동 내역입니다.")
    
    if not st.session_state.history_logs:
        st.info("아직 마감된 정산 장부 기록이 없습니다.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history_logs)):
            real_idx = len(st.session_state.history_logs) - 1 - idx
            
            with st.expander(f"[ {item.get('date', '날짜 미상')} ] - {item.get('mode', '3파전')} 결과", expanded=True):
                ranks_dict = item.get("ranks", {})
                
                st.markdown(f"> **[1위 우승]** {ranks_dict.get('1위', '정보 없음')}")
                if "3파전" in item.get('mode', '3파전'):
                    st.markdown(f"> **[2위]** {ranks_dict.get('2위', '정보 없음')}")
                    st.markdown(f"> **[3위]** {ranks_dict.get('3위', '정보 없음')}")
                else:
                    st.markdown(f"> **[2위]** {ranks_dict.get('2위', '정보 없음')}")
                    
                st.markdown("---")
                st.markdown("**세부 회비 및 MMR 변동표**")
                
                fine_table = []
                fines_dict = item.get("fines", {})
                for p_name, f_info in fines_dict.items():
                    mmr_c = f_info.get('mmr_change', 0)
                    mmr_str = f"+{mmr_c}" if mmr_c > 0 else str(mmr_c)
                    
                    fine_table.append({
                        "이름": p_name, 
                        "소속팀": f"{f_info.get('team', '미상')}", 
                        "순위": f"{f_info.get('rank', '-')}위", 
                        "벌금": f"{f_info.get('fine', 0)}원",
                        "MMR 증감": mmr_str
                    })
                if fine_table:
                    st.dataframe(pd.DataFrame(fine_table), use_container_width=True, hide_index=True)

                if is_admin:
                    if st.button("이 기록 삭제하기 (관리자 전용)", key=f"del_log_{real_idx}"):
                        item_to_delete = st.session_state.history_logs[real_idx]
                        for p_name, f_info in item_to_delete.get("fines", {}).items():
                            if p_name in st.session_state.MEMBER_DATABASE:
                                rollback_mmr = f_info.get("mmr_change", 0)
                                current_mmr = st.session_state.MEMBER_DATABASE[p_name].get("MMR", 1000)
                                st.session_state.MEMBER_DATABASE[p_name]["MMR"] = current_mmr - rollback_mmr
                                
                        st.session_state.history_logs.pop(real_idx)
                        save_permanent_data()
                        st.rerun()

# =========================================================================
# 4페이지
# =========================================================================
elif page == menu_4:
    st.title("4. 회원별 통계실 (MMR 랭킹)")
    st.write("정식 회원의 누적 승률 및 전투력 랭킹보드입니다.")
    st.caption("[안내] 종합 전투력(MMR)이 가장 높은 사람부터 내림차순 정렬됩니다.")
    
    stats_map = {}
    for name, db_info in st.session_state.MEMBER_DATABASE.items():
        stats_map[name] = {"MP": 0, "W": 0, "total_fine": 0, "MMR": int(db_info.get("MMR", 1000))}
        
    if st.session_state.history_logs:
        for item in st.session_state.history_logs:
            fines_dict = item.get("fines", {})
            for p_name, f_info in fines_dict.items():
                if p_name not in st.session_state.MEMBER_DATABASE:
                    continue
                
                stats_map[p_name]["MP"] += 1
                if f_info.get("rank") == 1:
                    stats_map[p_name]["W"] += 1
                stats_map[p_name]["total_fine"] += f_info.get("fine", 0)
            
    valid_players = {p: data for p, data in stats_map.items() if data["MP"] > 0}
    
    if valid_players:
        qual_players = {p: data for p, data in valid_players.items() if data["MP"] >= 3}
        if not qual_players:
            qual_players = valid_players
            
        att_sorted = sorted(valid_players.items(), key=lambda x: (x[1]['MP'], x[1]['W']), reverse=True)
        att_top3 = [(k, v['MP']) for k, v in att_sorted[:3]]

        win_sorted = sorted(qual_players.items(), key=lambda x: ((x[1]['W']/x[1]['MP']*100), x[1]['MP']), reverse=True)
        win_top3 = [(k, round(v['W']/v['MP']*100, 1)) for k, v in win_sorted[:3]]

        lose_sorted = sorted(qual_players.items(), key=lambda x: ((x[1]['W']/x[1]['MP']*100), -x[1]['MP']))
        lose_top3 = [(k, round(v['W']/v['MP']*100, 1)) for k, v in lose_sorted[:3]]

        fine_sorted = sorted(valid_players.items(), key=lambda x: (x[1]['total_fine'], x[1]['MP']), reverse=True)
        fine_top3 = [(k, v['total_fine']) for k, v in fine_sorted[:3] if v['total_fine'] > 0]
        
        st.markdown("### [ 몽말 명예 전당 ]")
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(make_podium_html("[ 몽말 지박령 ]", att_top3, "회"), unsafe_allow_html=True)
        with c2:
            st.markdown(make_podium_html("[ 버스기사 ]", win_top3, "%"), unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(make_podium_html("[ 혹시 스파이? ]", lose_top3, "%"), unsafe_allow_html=True)
        with c4:
            st.markdown(make_podium_html("[ 기부왕 ]", fine_top3, "원"), unsafe_allow_html=True)
            
        st.markdown("---")
            
    display_stats = []
    for p_name, s_data in stats_map.items():
        win_rate = (s_data["W"] / s_data["MP"] * 100) if s_data["MP"] > 0 else 0.0
        display_stats.append({
            "회원이름": p_name,
            "전투력(MMR)": s_data['MMR'],
            "참석": f"{s_data['MP']}주",
            "우승": f"{s_data['W']}회",
            "승률": f"{win_rate:.1f}%",
            "누적 벌금": f"{s_data['total_fine']}원"
        })
        
    df_stats = pd.DataFrame(display_stats)
    if df_stats.empty:
        st.info("아직 누적된 전적 데이터가 없습니다.")
    else:
        df_stats = df_stats.sort_values(by=["전투력(MMR)", "참석"], ascending=[False, False]).reset_index(drop=True)
        df_stats.index = range(1, len(df_stats) + 1)
        df_stats = df_stats.rename_axis("순위")
        
        st.dataframe(df_stats, use_container_width=True)

# =========================================================================
# 5페이지
# =========================================================================
else:
    st.title("5. 회원별 점수 관리실")
    
    st.subheader("신규 회원 대량 복붙 / 등록")
    st.write("엑셀 데이터를 [이름, 공격, 수비, 키퍼, MMR] 순서대로 복사해서 아래 표에 붙여넣기 하세요.")
    
    bulk_input_processed = st.session_state.bulk_input_df.copy()

    grid_bulk = st.data_editor(
        bulk_input_processed, num_rows="fixed", use_container_width=True, hide_index=True,
        column_config={
            "공격": st.column_config.NumberColumn(format="%.2f"),
            "수비": st.column_config.NumberColumn(format="%.2f"),
            "키퍼": st.column_config.NumberColumn(format="%.2f"),
            "MMR": st.column_config.NumberColumn(format="%d"),
        }
    )
    st.session_state.bulk_input_df = grid_bulk

    if st.button("도감에 신규 데이터 일괄 저장하기", use_container_width=True, type="primary"):
        saved_count = 0
        for _, row in grid_bulk.iterrows():
            name = str(row["이름"]).strip()
            if name and name != "None" and name != "":
                st.session_state.MEMBER_DATABASE[name] = {
                    "공격": safe_float(row.get("공격"), 3.0), 
                    "수비": safe_float(row.get("수비"), 3.0), 
                    "키퍼": safe_float(row.get("키퍼"), 3.0),
                    "MMR": safe_int(row.get("MMR"), 1000)
                }
                saved_count += 1
        if saved_count > 0:
            save_permanent_data()
            st.session_state.bulk_input_df = pd.DataFrame({"이름": [""] * 15, "공격": [3.0] * 15, "수비": [3.0] * 15, "키퍼": [3.0] * 15, "MMR": [1000] * 15})
            st.success("[성공] 총 데이터가 도감에 등록되었습니다.")
            st.rerun()
        else:
            st.error("입력된 이름이 없습니다.")
            
    st.markdown("---")
    
    st.subheader("등록된 도감 수정 및 삭제실")
    st.write("데이터를 수정하거나 삭제할 수 있습니다. 수동 점수 합계(공격+수비)가 높은 순서대로 표시됩니다.")
    st.caption("[안내] 작업 후 아래의 변경사항 저장 버튼을 눌러야 장부에 영구 반영됩니다.")
    
    db_list = []
    for name, stats in st.session_state.MEMBER_DATABASE.items():
        db_list.append({
            "이름": name, 
            "공격점수": safe_float(stats.get("공격", 0)), 
            "수비점수": safe_float(stats.get("수비", 0)), 
            "키퍼점수": safe_float(stats.get("키퍼", 0)),
            "MMR": safe_int(stats.get("MMR", 1000))
        })
    df_db = pd.DataFrame(db_list)
    
    if df_db.empty:
        st.info("현재 도감에 등록된 회원이 없습니다.")
    else:
        df_db['총점'] = df_db['공격점수'] + df_db['수비점수']
        df_db = df_db.sort_values(by=['총점', '공격점수'], ascending=[False, False]).drop(columns=['총점'])
        
        grid_master = st.data_editor(
            df_db, num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "이름": st.column_config.TextColumn(required=True),
                "공격점수": st.column_config.NumberColumn(format="%.2f"),
                "수비점수": st.column_config.NumberColumn(format="%.2f"),
                "키퍼점수": st.column_config.NumberColumn(format="%.2f"),
                "MMR": st.column_config.NumberColumn(format="%d"),
            }
        )
        
        if st.button("변경사항 도감에 최종 저장하기", use_container_width=True):
            new_database = {}
            for _, row in grid_master.iterrows():
                name = str(row["이름"]).strip()
                if name and name != "None" and name != "":
                    new_database[name] = {
                        "공격": safe_float(row.get("공격점수"), 3.0),
                        "수비": safe_float(row.get("수비점수"), 3.0),
                        "키퍼": safe_float(row.get("키퍼점수"), 3.0),
                        "MMR": safe_int(row.get("MMR"), 1000)
                    }
            st.session_state.MEMBER_DATABASE = new_database
            save_permanent_data()
            st.success("[성공] 도감의 수정 변경사항이 장부에 영구 저장되었습니다.")
            st.rerun()