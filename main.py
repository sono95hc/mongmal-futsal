import streamlit as st
import random
import pandas as pd

# 스마트폰 화면 및 브라우저 타이틀 설정
st.set_page_config(page_title="몽말 팀배분 프로그램 by홍찬", layout="centered")

# --- 여러 페이지 간 데이터 공유를 위한 저장소 세팅 ---
if "current_teams" not in st.session_state:
    st.session_state.current_teams = {}
if "match_mode" not in st.session_state:
    st.session_state.match_mode = "3파전"  # 기본값
if "edited_df" not in st.session_state:
    # ?? 명단 입력창도 한글로 깔끔하게 복구하되, 깨짐 방지를 위해 공백/괄호 최소화
    default_data = {
        "이름": ["손흥민", "이강인", "황희찬", "김민재", "조현우"] + [""] * 13,
        "공격": [5, 5, 4, 2, 1] + [1] * 13,
        "수비": [4, 3, 3, 5, 2] + [1] * 13,
        "키퍼": [2, 2, 1, 3, 5] + [1] * 13
    }
    st.session_state.edited_df = pd.DataFrame(default_data)
if "edited_score_df" not in st.session_state:
    quarters = [f"{i}쿼터" for i in range(1, 10)]
    score_data = {"블루": [0] * 9, "블랙": [0] * 9, "레드": [0] * 9}
    st.session_state.edited_score_df = pd.DataFrame(score_data, index=quarters)

# --- 스마트폰 메뉴 분리 ---
menu_1 = "1. 명단 및 팀배분"
menu_2 = "2. 경기 기록실"

st.sidebar.title("MENU")
page = st.sidebar.radio("메뉴를 선택하세요", [menu_1, menu_2])
st.sidebar.caption("제작자: by홍찬")

# --- 관리자 인증 시스템 ---
st.sidebar.markdown("---")
st.sidebar.subheader("관리자 인증")
admin_password = st.sidebar.text_input("비밀번호 입력", type="password")

is_admin = (admin_password == "1234")  # ?? 비밀번호 마스터키

# =========================================================================
# ?? 1페이지: 선수 명단 및 팀 배분 기능
# =========================================================================
if page == menu_1:
    if not is_admin:
        st.warning("이 페이지는 총무 전용입니다. 비밀번호를 입력하세요.")
    else:
        st.title("몽말 팀배분 프로그램")
        st.write("이름 칸에 이름, 공격/수비/키퍼 칸에 실력 점수(1~5)를 입력하세요.")
        
        # 선수 명단 엑셀 편집 창
        st.session_state.edited_df = st.data_editor(
            st.session_state.edited_df, num_rows="fixed", use_container_width=True, hide_index=True
        )

        st.markdown("---")
        st.subheader("경기 방식 설정")
        selected_mode = st.radio("오늘 매치 방식을 골라주세요", ["2파전 (8쿼터)", "3파전 (9쿼터)"])

        # 팀 짜기 버튼
        if st.button("팀 짜기 시작", use_container_width=True, type="primary"):
            players = []
            for _, row in st.session_state.edited_df.iterrows():
                name = str(row["이름"]).strip()
                if name and name != "None" and name != "":
                    players.append({"name": name, "total": int(row["공격"]) + int(row["수비"])})
                    
            total_players = len(players)
            if total_players < 2:
                st.error("선수를 입력해 주세요.")
            else:
                players.sort(key=lambda x: x['total'], reverse=True)
                
                if "2파전" in selected_mode:
                    st.session_state.match_mode = "2파전"
                    team_names = ["레드", "블루"]
                    st.session_state.current_teams = {name: [] for name in team_names}
                    
                    for idx, p in enumerate(players):
                        st.session_state.current_teams["레드" if idx % 2 == 0 else "블루"].append(p)
                    
                    quarters_2p = [f"{i}쿼터" for i in range(1, 9)]
                    score_data_2p = {"블루": [0] * 8, "레드": [0] * 8}
                    st.session_state.edited_score_df = pd.DataFrame(score_data_2p, index=quarters_2p)
                else:
                    st.session_state.match_mode = "3파전"
                    team_names = ["블랙", "레드", "블루"]
                    st.session_state.current_teams = {name: [] for name in team_names}
                    
                    order = [0, 1, 2]
                    for idx, p in enumerate(players):
                        if idx % 3 == 0 and idx > 0: random.shuffle(order)
                        st.session_state.current_teams[team_names[order[idx % 3]]].append(p)
                    
                    quarters_3p = [f"{i}쿼터" for i in range(1, 10)]
                    score_data_3p = {"블루": [0] * 9, "블랙": [0] * 9, "레드": [0] * 9}
                    st.session_state.edited_score_df = pd.DataFrame(score_data_3p, index=quarters_3p)

        # 팀 짜기 결과 출력
        if st.session_state.current_teams:
            st.success(f"매칭 완료")
            katalk_text = f"[풋살 팀 매칭 결과 ({st.session_state.match_mode})]\n"
            for t_name, members in st.session_state.current_teams.items():
                m_names = [p['name'] for p in members]
                katalk_text += f"\n- {t_name}팀 ({len(members)}명)\n  : {', '.join(m_names)}\n"
            st.text_area("꾹 눌러서 복사 후 카톡 공지", value=katalk_text, height=140)

# =========================================================================
# ?? 2페이지: 경기 기록실 (모든 회원이 상시 보는 화면)
# =========================================================================
else:
    st.title(f"실시간 경기 기록실 ({st.session_state.match_mode})")
    st.write("각 쿼터별 스코어를 입력하세요. 쉬는 팀은 점수를 0으로 두면 됩니다.")
        
    st.session_state.edited_score_df = st.data_editor(st.session_state.edited_score_df, use_container_width=True)

    if st.session_state.match_mode == "2파전":
        history_keys = ["레드", "블루"]
    else:
        history_keys = ["레드", "블랙", "블루"]

    history = {t: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS": 0, "MP": 0} for t in history_keys}
    loop_count = 8 if st.session_state.match_mode == "2파전" else 9

    for i in range(loop_count):
        blue_score = st.session_state.edited_score_df.iloc[i]["블루"]
        red_score = st.session_state.edited_score_df.iloc[i]["레드"]
        black_score = st.session_state.edited_score_df.iloc[i]["블랙"] if st.session_state.match_mode == "3파전" else 0
        
        t_pairs = []
        scores = []
        
        if st.session_state.match_mode == "2파전":
            t_pairs = ["레드", "블루"]
            scores = [int(red_score), int(blue_score)]
            if blue_score == 0 and red_score == 0: continue
        else:
            if i % 3 == 0:
                t_pairs = ["레드", "블루"]; scores = [int(red_score), int(blue_score)]
                if black_score > 0 and red_score == 0: t_pairs = ["블랙", "블루"]; scores = [int(black_score), int(blue_score)]
                elif black_score > 0 and blue_score == 0: t_pairs = ["블랙", "레드"]; scores = [int(black_score), int(red_score)]
            elif i % 3 == 1:
                t_pairs = ["블랙", "레드"]; scores = [int(black_score), int(red_score)]
                if blue_score > 0 and black_score == 0: t_pairs = ["블루", "레드"]; scores = [int(blue_score), int(red_score)]
                elif blue_score > 0 and red_score == 0: t_pairs = ["블루", "블랙"]; scores = [int(blue_score), int(black_score)]
            else:
                t_pairs = ["블루", "블랙"]; scores = [int(blue_score), int(black_score)]
                if red_score > 0 and blue_score == 0: t_pairs = ["레드", "블랙"]; scores = [int(red_score), int(black_score)]
                elif red_score > 0 and black_score == 0: t_pairs = ["레드", "블루"]; scores = [int(red_score), int(blue_score)]

            if scores[0] == 0 and scores[1] == 0 and (blue_score == 0 and black_score == 0 and red_score == 0):
                continue
            
        tm1, tm2 = t_pairs[0], t_pairs[1]
        sc1, sc2 = scores[0], scores[1]
        
        history[tm1]["MP"] += 1; history[tm2]["MP"] += 1
        history[tm1]["GF"] += sc1; history[tm1]["GA"] += sc2
        history[tm2]["GF"] += sc2; history[tm2]["GA"] += sc1
        
        if sc1 > sc2:
            history[tm1]["W"] += 1; history[tm1]["PTS"] += 3
            history[tm2]["L"] += 1
        elif sc1 < sc2:
            history[tm2]["W"] += 1; history[tm2]["PTS"] += 3
            history[tm1]["L"] += 1
        else:
            history[tm1]["W"] += 0; history[tm1]["D"] += 1; history[tm1]["PTS"] += 1
            history[tm2]["W"] += 0; history[tm2]["D"] += 1; history[tm2]["PTS"] += 1

    for t in history:
        history[t]["GD"] = history[t]["GF"] - history[t]["GA"]

    st.subheader("오늘 경기 실시간 순위표")

    sort_df = pd.DataFrame([
        {"팀": t, "PTS": history[t]["PTS"], "GD": history[t]["GD"], "GF": history[t]["GF"]} 
        for t in history_keys
    ])
    sort_df = sort_df.sort_values(by=["PTS", "GD", "GF"], ascending=[False, False, False]).reset_index(drop=True)

    final_display = []
    for idx, row in sort_df.iterrows():
        t_name = row["팀"]
        stat = history[t_name]
        # ?? [한글 복구 완료] 가독성을 위해 완벽하게 직관적인 우리말 단어로 수정했습니다.
        final_display.append({
            "순위": f"{idx+1}위",
            "팀명": f"{t_name}팀",
            "경기수": f"{stat['MP']}전",
            "승 - 무 - 패": f"{stat['W']}승 - {stat['D']}무 - {stat['L']}패",
            "승점": f"{stat['PTS']}점",
            "득실차 (득/실)": f"{stat['GD']} ({stat['GF']}/{stat['GA']})"
        })

    st.table(pd.DataFrame(final_display).set_index("순위"))