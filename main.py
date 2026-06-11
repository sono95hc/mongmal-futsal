import streamlit as st
import random
import pandas as pd

# 스마트폰 화면 및 브라우저 타이틀 설정
st.set_page_config(page_title="몽말 팀배분 프로그램 by홍찬", layout="centered")

# --- 여러 페이지 간 데이터 공유를 위한 저장소 세팅 ---
if "current_teams" not in st.session_state:
    st.session_state.current_teams = {}
if "match_mode" not in st.session_state:
    st.session_state.match_mode = "3파전"

# ?? [회원별 점수 도감] 최초 기본 데이터베이스 세팅
if "MEMBER_DATABASE" not in st.session_state:
    st.session_state.MEMBER_DATABASE = {
        "손흥민": {"공격": 5, "수비": 4, "키퍼": 2},
        "이강인": {"공격": 5, "수비": 3, "키퍼": 2},
        "황희찬": {"공격": 4, "수비": 3, "키퍼": 1},
        "김민재": {"공격": 2, "수비": 5, "키퍼": 3},
        "조현우": {"공격": 1, "수비": 2, "키퍼": 5}
    }

# --- 명단 입력창 초기 데이터 세팅 (이름만 관리) ---
if "attendance_list" not in st.session_state:
    st.session_state.attendance_list = ["손흥민", "이강인", "황희찬", "김민재", "조현우"] + [""] * 13

if "edited_score_df" not in st.session_state:
    quarters = [f"{i}쿼터" for i in range(1, 10)]
    score_data = {"블루": [0] * 9, "블랙": [0] * 9, "레드": [0] * 9}
    st.session_state.edited_score_df = pd.DataFrame(score_data, index=quarters)

# --- 스마트폰 메뉴 구조 정의 ---
menu_1 = "1. 명단 및 팀배분"
menu_2 = "2. 경기 기록실"
menu_3 = "3. 회원별 점수"  # ?? [이름 변경 및 비공개 대상]

st.sidebar.title("MENU")

# --- ?? 관리자 인증 시스템 ---
st.sidebar.markdown("---")
st.sidebar.subheader("관리자 인증")
admin_password = st.sidebar.text_input("비밀번호 입력", type="password")
is_admin = (admin_password == "1234")  # ?? 총무 전용 패스워드

# ?? [메뉴 권한 쪼개기] 관리자가 아니어도 1번, 2번은 상시 노출! 3번만 숨김!
if is_admin:
    menu_options = [menu_1, menu_2, menu_3]
else:
    menu_options = [menu_1, menu_2]

page = st.sidebar.radio("메뉴를 선택하세요", menu_options)
st.sidebar.caption("제작자: by홍찬")

# =========================================================================
# ?? 1페이지: 선수 명단 및 팀 배분 기능 (일반 회원 상시 오픈 버전)
# =========================================================================
if page == menu_1:
    st.title("몽말 팀배분 프로그램")
    st.write("오늘 참석한 선수들의 이름을 차례대로 입력하세요. (최대 18명)")
    
    # ?? [보안의 핵심] 점수 칸은 아예 노출하지 않고 오직 '이름'만 들어있는 단일 열 표를 만듭니다.
    df_attendance = pd.DataFrame({"이름": st.session_state.attendance_list})
    
    grid_result = st.data_editor(
        df_attendance, num_rows="fixed", use_container_width=True, hide_index=True
    )
    
    # 입력받은 이름을 실시간 세션에 저장
    st.session_state.attendance_list = grid_result["이름"].tolist()

    st.markdown("---")
    st.subheader("경기 방식 설정")
    selected_mode = st.radio("오늘 매치 방식을 골라주세요", ["2파전 (8쿼터)", "3파전 (9쿼터)"])

    if st.button("팀 짜기 시작", use_container_width=True, type="primary"):
        players = []
        for name in st.session_state.attendance_list:
            cleaned_name = str(name).strip()
            if cleaned_name and cleaned_name != "None" and cleaned_name != "":
                # ?? [연동 엔진] 화면에는 이름만 보이지만, 컴퓨터가 내부 도감(DB)에서 점수를 몰래 조회함!
                if cleaned_name in st.session_state.MEMBER_DATABASE:
                    db_info = st.session_state.MEMBER_DATABASE[cleaned_name]
                    total_score = int(db_info["공격"]) + int(db_info["수비"])
                else:
                    # 도감에 없는 신규 회원은 기본 평점(중간 점수인 공격3+수비3 = 6점) 부여
                    total_score = 6
                
                players.append({"name": cleaned_name, "total": total_score})
                
        total_players = len(players)
        if total_players < 2:
            st.error("선수를 입력해 주세요.")
        else:
            # 실력 점수 순으로 정렬하여 황금 밸런스 분배 진행
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

    if st.session_state.current_teams:
        st.success(f"매칭 완료")
        katalk_text = f"[풋살 팀 매칭 결과 ({st.session_state.match_mode})]\n"
        for t_name, members in st.session_state.current_teams.items():
            m_names = [p['name'] for p in members]
            katalk_text += f"\n- {t_name}팀 ({len(members)}명)\n  : {', '.join(m_names)}\n"
        st.text_area("꾹 눌러서 복사 후 카톡 공지", value=katalk_text, height=140)

# =========================================================================
# ?? 2페이지: 경기 기록실 (모든 회원 상시 오픈)
# =========================================================================
elif page == menu_2:
    st.title(f"실시간 경기 기록실 ({st.session_state.match_mode})")
    st.write("각 쿼터별 스코어를 입력하세요. 쉬는 팀은 점수를 0으로 두면 됩니다.")
    st.session_state.edited_score_df = st.data_editor(st.session_state.edited_score_df, use_container_width=True)

    history_keys = ["레드", "블루"] if st.session_state.match_mode == "2파전" else ["레드", "블랙", "블루"]
    history = {t: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS": 0, "MP": 0} for t in history_keys}
    loop_count = 8 if st.session_state.match_mode == "2파전" else 9

    for i in range(loop_count):
        blue_score = st.session_state.edited_score_df.iloc[i]["블루"]
        red_score = st.session_state.edited_score_df.iloc[i]["레드"]
        black_score = st.session_state.edited_score_df.iloc[i]["블랙"] if st.session_state.match_mode == "3파전" else 0
        
        t_pairs = []
        scores = []
        
        if st.session_state.match_mode == "2파전":
            t_pairs = ["레드", "블루"]; scores = [int(red_score), int(blue_score)]
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

# =========================================================================
# ? 3페이지: 회원별 점수 등록 및 조회창 (총무 인증시에만 노출 및 진입 가능)
# =========================================================================
else:
    st.title("3. 회원별 점수 관리실")
    st.write("비공개 도감 구역입니다. 여기에 등록된 회원 점수를 토대로 앞 페이지에서 밸런스 팀 매칭이 진행됩니다.")
    
    # 새로운 데이터 입력 폼
    new_name = st.text_input("회원 이름 입력").strip()
    new_atk = st.slider("공격 능력치", 1, 5, 3)
    new_dfd = st.slider("수비 능력치", 1, 5, 3)
    new_gk = st.slider("키퍼 능력치", 1, 5, 3)
    
    if st.button("도감에 데이터 저장하기", use_container_width=True, type="primary"):
        if not new_name:
            st.error("이름을 입력해 주세요.")
        else:
            st.session_state.MEMBER_DATABASE[new_name] = {
                "공격": new_atk, "수비": new_dfd, "키퍼": new_gk
            }
            st.success(f"성공! [ {new_name} ] 선수의 실력 데이터가 비공개 저장소에 기록되었습니다.")
            
    st.markdown("---")
    st.subheader("현재 등록된 전체 회원별 점수 도감")
    db_list = []
    for name, stats in st.session_state.MEMBER_DATABASE.items():
        db_list.append({"이름": name, "공격점수": stats["공격"], "수비점수": stats["수비"], "키퍼점수": stats["키퍼"]})
    st.dataframe(pd.DataFrame(db_list), use_container_width=True, hide_index=True)