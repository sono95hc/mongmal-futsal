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

# [보안/규격 완벽 수정] 깃허브 백업 엔진
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
    if mode == "2파전":
        quarters = [f"{i}쿼터" for i in range(1, 9)]
        return pd.DataFrame({"블루": [None] * 8, "레드": [None] * 8}, index=quarters)
    else:
        quarters = [f"{i}쿼터" for i in range(1, 10)]
        return pd.DataFrame({"블루": [None] * 9, "블랙": [None] * 9, "레드": [None] * 9}, index=quarters)

def load_permanent_data():
    default_data = {
        "MEMBER_DATABASE": {
            "손흥민": {"공격": 5.0, "수비": 4.0, "키퍼": 2.0},
            "이강인": {"공격": 5.0, "수비": 3.0, "키퍼": 2.0},
            "황희찬": {"공격": 4.0, "수비": 3.0, "키퍼": 1.0},
            "김민재": {"공격": 2.0, "수비": 5.0, "키퍼": 3.0},
            "조현우": {"공격": 1.0, "수비": 2.0, "키퍼": 5.0}
        },
        "attendance_list": ["손흥민", "이강인", "황희찬", "김민재", "조현우"],
        "match_mode": "3파전",
        "score_data_dict": get_blank_score_df("3파전").to_dict(orient="list"),
        "history_logs": [],
        "current_teams": {},
        "current_q_idx": 0
    }

    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                if "MEMBER_DATABASE" not in data: data["MEMBER_DATABASE"] = default_data["MEMBER_DATABASE"]
                if "attendance_list" not in data: data["attendance_list"] = default_data["attendance_list"]
                if "match_mode" not in data: data["match_mode"] = "3파전"
                if "score_data_dict" not in data: data["score_data_dict"] = default_data["score_data_dict"]
                if "history_logs" not in data: data["history_logs"] = []
                if "current_teams" not in data: data["current_teams"] = {}
                if "current_q_idx" not in data: data["current_q_idx"] = 0
                    
                if "경기팀" in data["score_data_dict"]:
                    del data["score_data_dict"]["경기팀"]
                    
                return data
        except:
            pass
            
    return default_data

def save_permanent_data():
    score_dict = st.session_state.edited_score_df.to_dict(orient="list")
    clean_attendance = [x for x in st.session_state.attendance_list if x.strip()]
    data_to_save = {
        "MEMBER_DATABASE": st.session_state.MEMBER_DATABASE,
        "attendance_list": clean_attendance,
        "match_mode": st.session_state.match_mode,
        "score_data_dict": score_dict,
        "history_logs": st.session_state.get("history_logs", []),
        "current_teams": st.session_state.get("current_teams", {}),
        "current_q_idx": st.session_state.get("current_q_idx", 0)
    }
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        
    json_str = json.dumps(data_to_save, ensure_ascii=False, indent=4)
    push_to_github(json_str)

perm_data = load_permanent_data()

if "MEMBER_DATABASE" not in st.session_state: st.session_state.MEMBER_DATABASE = perm_data["MEMBER_DATABASE"]
if "attendance_list" not in st.session_state: st.session_state.attendance_list = [x for x in perm_data["attendance_list"] if x.strip()]
if "match_mode" not in st.session_state: st.session_state.match_mode = perm_data["match_mode"]
if "history_logs" not in st.session_state: st.session_state.history_logs = perm_data["history_logs"]
if "current_teams" not in st.session_state: st.session_state.current_teams = perm_data.get("current_teams", {})
if "current_q_idx" not in st.session_state: st.session_state.current_q_idx = perm_data.get("current_q_idx", 0)

if "ai_teams" not in st.session_state:
    st.session_state.ai_teams = {}

if "edited_score_df" not in st.session_state:
    mode = st.session_state.match_mode
    quarters = [f"{i}쿼터" for i in range(1, 8 if mode == "2파전" else 10)]
    st.session_state.edited_score_df = pd.DataFrame(perm_data["score_data_dict"], index=quarters)

if "temp_match_type" not in st.session_state:
    st.session_state.temp_match_type = "블루 vs 레드"
if "bulk_input_df" not in st.session_state:
    st.session_state.bulk_input_df = pd.DataFrame({
        "이름": [""] * 15, "공격": [3.0] * 15, "수비": [3.0] * 15, "키퍼": [3.0] * 15
    })
if "show_warning" not in st.session_state:
    st.session_state.show_warning = False
if "confirm_close" not in st.session_state:
    st.session_state.confirm_close = False

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
    
    st.subheader("[1단계] 참석자 입력")
    st.write("오늘 참석한 선수들의 이름을 띄어쓰기로 구분하여 적어주세요.")
    
    current_att_str = " ".join([x for x in st.session_state.attendance_list if x])
    att_input = st.text_area("명단 입력 (예: 손흥민 이강인 황희찬)", value=current_att_str, height=100)
    
    raw_att_list = [x.strip() for x in att_input.split() if x.strip()]
    current_att_list = []
    for x in raw_att_list:
        if x not in current_att_list:
            current_att_list.append(x)
            
    if current_att_list != st.session_state.attendance_list:
        st.session_state.attendance_list = current_att_list
        save_permanent_data()
        
    st.markdown("---")
    st.subheader("[2단계] 경기 방식 설정")
    selected_mode = st.radio("오늘 매치 방식을 골라주세요", ["2파전 (8쿼터)", "3파전 (9쿼터)"], index=0 if st.session_state.match_mode == "2파전" else 1)
    team_options = ["미배정", "레드", "블루"] if "2파전" in selected_mode else ["미배정", "블랙", "레드", "블루"]

    st.markdown("---")
    st.subheader("[3단계] 팀 편성 (자동+수동 조합)")
    st.write("AI 버튼을 누르면 실력, 이전 매치 전적(승률), 지난주 조합을 종합 분석하여 배분됩니다.")
    
    if st.button("AI 자동 밸런스 매칭 가동", use_container_width=True):
        # 1. 지난주 팀 추적 로직
        prev_teams = {}
        if st.session_state.history_logs:
            last_log = st.session_state.history_logs[-1]
            for p_name, f_info in last_log.get("fines", {}).items():
                prev_teams[p_name] = f_info.get("team")
                
        # 2. 통계실 기반 승률 맵핑 (10판 이상인 경우 승률 50% 수렴을 위한 밸런싱)
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
            if name in st.session_state.MEMBER_DATABASE:
                db_info = st.session_state.MEMBER_DATABASE[name]
                base_score = float(db_info.get("공격", 0)) + float(db_info.get("수비", 0))
            
            effective_score = base_score
            # [핵심 로직] 10판 이상 참여자 승률 기반 핸디캡/버프 적용 (±최대 1.5점 가감)
            if name in stats_map:
                mp = stats_map[name]["MP"]
                w = stats_map[name]["W"]
                if mp >= 10:
                    win_rate = (w / mp) * 100
                    effective_score += (win_rate - 50) * 0.03 
                    
            players.append({"name": name, "total": effective_score})
            
        # 평가 점수를 기준으로 내림차순 정렬 후 순차 분배 분산 최적화 연산
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
                
                for p, t in zip(chunk, perm):
                    temp_team_sums[t] += p["total"]
                    for existing_p in new_teams[t]:
                        m1, m2 = p["name"], existing_p["name"]
                        if m1 in prev_teams and m2 in prev_teams and prev_teams[m1] == prev_teams[m2]:
                            same_team_penalty += 15.0 # 지난주 같은 팀 회피 강력 패널티
                            
                avg_sum = sum(temp_team_sums.values()) / len(teams_keys)
                variance = sum((s - avg_sum)**2 for s in temp_team_sums.values())
                
                # 동일팀 패널티와 팀 점수 분산(Variance)을 동시 최소화
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
            
        st.rerun()

    final_team_selections = {}
    if current_att_list:
        cols = st.columns(2)
        for idx, player_name in enumerate(current_att_list):
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
            katalk_text += f"\n{t_name}팀 ({len(members)}명)\n{', '.join(m_names)}\n"
            
        st.text_area("복사 후 카톡 공지용 텍스트", value=katalk_text, height=140)


# =========================================================================
# 2페이지
# =========================================================================
elif page == menu_2:
    st.title(f"실시간 경기 기록실 ({st.session_state.match_mode})")
    
    st.subheader("쿼터 스코어 입력창")
    st.write("저장 시 자동으로 다음 쿼터로 넘어가며, 언제든 박스를 눌러 이전 쿼터를 수정할 수 있습니다.")
    
    loop_count = 8 if st.session_state.match_mode == "2파전" else 9
    quarter_options = [f"{i}쿼터" for i in range(1, loop_count + 1)]
    
    selected_q = st.selectbox("기록할 쿼터 선택", quarter_options, index=st.session_state.current_q_idx)
    st.session_state.current_q_idx = quarter_options.index(selected_q)
    
    current_q_data = st.session_state.edited_score_df.loc[selected_q]
    
    val_blue = None
    val_black = None
    val_red = None
    
    if st.session_state.match_mode == "3파전":
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
        if st.session_state.match_mode == "3파전":
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
    st.dataframe(display_score_df, use_container_width=True)

    history_keys = ["레드", "블루"] if st.session_state.match_mode == "2파전" else ["레드", "블랙", "블루"]
    history = {t: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS": 0, "MP": 0} for t in history_keys}

    for i in range(loop_count):
        row_data = st.session_state.edited_score_df.iloc[i]
        b_val = row_data.get("블루")
        r_val = row_data.get("레드")
        bl_val = row_data.get("블랙") if st.session_state.match_mode == "3파전" else None
        
        valid_teams = []
        valid_scores = []
        
        if pd.notna(b_val): valid_teams.append("블루"); valid_scores.append(int(b_val))
        if pd.notna(r_val): valid_teams.append("레드"); valid_scores.append(int(r_val))
        if bl_val is not None and pd.notna(bl_val): valid_teams.append("블랙"); valid_scores.append(int(bl_val))
        
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

    if st.session_state.current_teams:
        st.markdown("---")
        st.subheader("오늘의 정산 마감 구역")
        st.write("모든 쿼터 입력이 끝났다면 아래 버튼을 눌러 날짜별 장부에 오늘 전적과 벌금을 저장하세요.")
        
        if st.button("오늘 경기 정산 및 마감하기", use_container_width=True, type="primary"):
            st.session_state.confirm_close = True
            
        if st.session_state.confirm_close:
            st.warning("[확인] 정말 오늘 경기를 마감하시겠습니까? (마감 시 3번 메뉴로 데이터가 영구 저장됩니다)")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("네, 마감합니다", use_container_width=True):
                    now_utc = datetime.utcnow()
                    now_kst = now_utc + timedelta(hours=9)
                    today_str = now_kst.strftime("%Y-%m-%d %H:%M")
                    
                    ranked_teams = sort_df["팀"].tolist()
                    
                    log_entry = {
                        "date": today_str,
                        "mode": st.session_state.match_mode,
                        "ranks": {},
                        "fines": {}
                    }
                    
                    for rank_idx, t_name in enumerate(ranked_teams):
                        rank_num = rank_idx + 1
                        team_players = [p["name"] for p in st.session_state.current_teams.get(t_name, [])]
                        log_entry["ranks"][f"{rank_num}위"] = f"{t_name}팀 ({', '.join(team_players)})"
                        
                        if st.session_state.match_mode == "2파전":
                            fine_amount = 0 if rank_num == 1 else 2000
                        else:
                            if rank_num == 1: fine_amount = 0
                            elif rank_num == 2: fine_amount = 1000
                            else: fine_amount = 2000
                            
                        for p_name in team_players:
                            log_entry["fines"][p_name] = {"team": t_name, "rank": rank_num, "fine": fine_amount}
                    
                    st.session_state.history_logs.append(log_entry)
                    save_permanent_data()
                    st.session_state.confirm_close = False
                    st.success("정산 완료. 기록이 안전하게 저장되었습니다.")
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
    st.write("매주 마감된 경기 결과와 개인별 회비 내역이 누적되는 공간입니다.")
    
    if not st.session_state.history_logs:
        st.info("아직 마감된 정산 장부 기록이 없습니다.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history_logs)):
            real_idx = len(st.session_state.history_logs) - 1 - idx
            
            with st.expander(f"[ {item.get('date', '날짜 미상')} ] - {item.get('mode', '3파전')} 결과", expanded=True):
                ranks_dict = item.get("ranks", {})
                
                st.markdown(f"> **[1위 우승]** {ranks_dict.get('1위', '정보 없음')}")
                if item.get('mode', '3파전') == "3파전":
                    st.markdown(f"> **[2위]** {ranks_dict.get('2위', '정보 없음')}")
                    st.markdown(f"> **[3위]** {ranks_dict.get('3위', '정보 없음')}")
                else:
                    st.markdown(f"> **[2위]** {ranks_dict.get('2위', '정보 없음')}")
                    
                st.markdown("---")
                st.markdown("**세부 회비 정산표**")
                
                fine_table = []
                fines_dict = item.get("fines", {})
                for p_name, f_info in fines_dict.items():
                    fine_table.append({
                        "이름": p_name, 
                        "소속팀": f"{f_info.get('team', '미상')}", 
                        "순위": f"{f_info.get('rank', '-')}위", 
                        "벌금": f"{f_info.get('fine', 0)}원"
                    })
                if fine_table:
                    st.dataframe(pd.DataFrame(fine_table), use_container_width=True, hide_index=True)

                if is_admin:
                    if st.button("이 기록 삭제하기 (관리자 전용)", key=f"del_log_{real_idx}"):
                        st.session_state.history_logs.pop(real_idx)
                        save_permanent_data()
                        st.rerun()

# =========================================================================
# 4페이지
# =========================================================================
elif page == menu_4:
    st.title("4. 회원별 통계실")
    st.write("정식 등록 회원의 누적 승률 및 회비 현황입니다.")
    st.caption("[안내] 5번 메뉴에 등록되지 않은 일일 용병은 자동으로 제외됩니다.")
    
    stats_map = {}
    for name in st.session_state.MEMBER_DATABASE.keys():
        stats_map[name] = {"MP": 0, "W": 0, "total_fine": 0}
        
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
            
    display_stats = []
    for p_name, s_data in stats_map.items():
        win_rate = (s_data["W"] / s_data["MP"] * 100) if s_data["MP"] > 0 else 0.0
        display_stats.append({
            "회원이름": p_name,
            "참석": f"{s_data['MP']}주",
            "우승": f"{s_data['W']}회",
            "승률": f"{win_rate:.1f}%",
            "누적 벌금": f"{s_data['total_fine']}원"
        })
        
    df_stats = pd.DataFrame(display_stats)
    if df_stats.empty:
        st.info("아직 누적된 전적 데이터가 없습니다.")
    else:
        df_stats = df_stats.sort_values(by=["우승", "참석"], ascending=[False, False]).reset_index(drop=True)
        df_stats.index = range(1, len(df_stats) + 1)
        df_stats = df_stats.rename_axis("순위")
        
        st.dataframe(df_stats, use_container_width=True)

# =========================================================================
# 5페이지
# =========================================================================
else:
    st.title("5. 회원별 점수 관리실")
    
    st.subheader("신규 회원 대량 복붙 / 등록")
    st.write("엑셀 데이터를 [이름, 공격, 수비, 키퍼] 순서대로 복사해서 아래 표 첫 칸에 붙여넣기 하세요.")
    
    bulk_input_processed = st.session_state.bulk_input_df.copy()
    bulk_input_processed["공격"] = bulk_input_processed["공격"].astype(float)
    bulk_input_processed["수비"] = bulk_input_processed["수비"].astype(float)
    bulk_input_processed["키퍼"] = bulk_input_processed["키퍼"].astype(float)

    grid_bulk = st.data_editor(
        bulk_input_processed, num_rows="fixed", use_container_width=True, hide_index=True,
        column_config={
            "공격": st.column_config.NumberColumn(format="%.2f"),
            "수비": st.column_config.NumberColumn(format="%.2f"),
            "키퍼": st.column_config.NumberColumn(format="%.2f"),
        }
    )
    st.session_state.bulk_input_df = grid_bulk

    if st.button("도감에 신규 데이터 일괄 저장하기", use_container_width=True, type="primary"):
        saved_count = 0
        for _, row in grid_bulk.iterrows():
            name = str(row["이름"]).strip()
            if name and name != "None" and name != "":
                st.session_state.MEMBER_DATABASE[name] = {
                    "공격": round(float(row["공격"]), 2), "수비": round(float(row["수비"]), 2), "키퍼": round(float(row["키퍼"]), 2)
                }
                saved_count += 1
        if saved_count > 0:
            save_permanent_data()
            st.session_state.bulk_input_df = pd.DataFrame({"이름": [""] * 15, "공격": [3.0] * 15, "수비": [3.0] * 15, "키퍼": [3.0] * 15})
            st.success(f"[성공] 총 {saved_count}명의 데이터가 도감에 등록되었습니다.")
            st.rerun()
        else:
            st.error("입력된 이름이 없습니다.")
            
    st.markdown("---")
    
    st.subheader("등록된 도감 수정 및 삭제실")
    st.write("아래 표에서 데이터를 직접 수정하거나, 행 왼쪽을 누르고 키보드 Delete 키를 눌러 삭제할 수 있습니다.")
    st.caption("작업 후 아래의 [변경사항 도감에 최종 저장하기] 버튼을 눌러야 장부에 영구 반영됩니다.")
    
    db_list = []
    for name, stats in st.session_state.MEMBER_DATABASE.items():
        db_list.append({
            "이름": name, 
            "공격점수": round(float(stats["공격"]), 2), 
            "수비점수": round(float(stats["수비"]), 2), 
            "키퍼점수": round(float(stats["키퍼"]), 2)
        })
    df_db = pd.DataFrame(db_list)
    
    if df_db.empty:
        st.info("현재 도감에 등록된 회원이 없습니다.")
    else:
        # [도감 정렬 패치] 총점(공격+수비) 기준 내림차순 정렬 적용
        df_db['총점'] = df_db['공격점수'] + df_db['수비점수']
        df_db = df_db.sort_values(by=['총점', '공격점수'], ascending=[False, False]).drop(columns=['총점'])
        
        grid_master = st.data_editor(
            df_db, num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "이름": st.column_config.TextColumn(required=True),
                "공격점수": st.column_config.NumberColumn(format="%.2f"),
                "수비점수": st.column_config.NumberColumn(format="%.2f"),
                "키퍼점수": st.column_config.NumberColumn(format="%.2f"),
            }
        )
        
        if st.button("변경사항 도감에 최종 저장하기", use_container_width=True):
            new_database = {}
            for _, row in grid_master.iterrows():
                name = str(row["이름"]).strip()
                if name and name != "None" and name != "":
                    new_database[name] = {
                        "공격": round(float(row["공격점수"]), 2),
                        "수비": round(float(row["수비점수"]), 2),
                        "키퍼": round(float(row["키퍼점수"]), 2)
                    }
            st.session_state.MEMBER_DATABASE = new_database
            save_permanent_data()
            st.success("[성공] 도감의 수정 변경사항이 장부에 영구 저장되었습니다.")
            st.rerun()