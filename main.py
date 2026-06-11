import streamlit as st
import random
import pandas as pd
import json
import os

# 스마트폰 화면 및 브라우저 타이틀 설정
st.set_page_config(page_title="몽말 팀배분 프로그램 by홍찬", layout="centered")

# --- ?? [파일 영구 저장 엔진] 시스템 설정 ---
DB_FILE = "futsal_data.json"

# 초기 데이터 구조 정의
def get_blank_score_df(mode="3파전"):
    if mode == "2파전":
        quarters = [f"{i}쿼터" for i in range(1, 9)]
        return pd.DataFrame({"블루": [0] * 8, "레드": [0] * 8}, index=quarters)
    else:
        quarters = [f"{i}쿼터" for i in range(1, 10)]
        return pd.DataFrame({"블루": [0] * 9, "블랙": [0] * 9, "레드": [0] * 9}, index=quarters)

# 1. 파일에서 데이터 읽어오기 함수
def load_permanent_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "MEMBER_DATABASE" not in data:
                    data["MEMBER_DATABASE"] = {
                        "손흥민": {"공격": 5, "수비": 4, "키퍼": 2},
                        "이강인": {"공격": 5, "수비": 3, "키퍼": 2},
                        "황희찬": {"공격": 4, "수비": 3, "키퍼": 1},
                        "김민재": {"공격": 2, "수비": 5, "키퍼": 3},
                        "조현우": {"공격": 1, "수비": 2, "키퍼": 5}
                    }
                return data
        except:
            pass
    
    return {
        "MEMBER_DATABASE": {
            "손흥민": {"공격": 5, "수비": 4, "키퍼": 2},
            "이강인": {"공격": 5, "수비": 3, "키퍼": 2},
            "황희찬": {"공격": 4, "수비": 3, "키퍼": 1},
            "김민재": {"공격": 2, "수비": 5, "키퍼": 3},
            "조현우": {"공격": 1, "수비": 2, "키퍼": 5}
        },
        "attendance_list": ["손흥민", "이강인", "황희찬", "김민재", "조현우"] + [""] * 13,
        "match_mode": "3파전",
        "score_data_dict": get_blank_score_df("3파전").to_dict(orient="list")
    }

# 2. 파일에 데이터 영구 저장하기 함수
def save_permanent_data():
    score_dict = st.session_state.edited_score_df.to_dict(orient="list")
    data_to_save = {
        "MEMBER_DATABASE": st.session_state.MEMBER_DATABASE,
        "attendance_list": st.session_state.attendance_list,
        "match_mode": st.session_state.match_mode,
        "score_data_dict": score_dict
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# --- 최초 진입 시 장부에서 데이터를 싹 긁어와 세션에 상주 시킴 ---
if "initialized" not in st.session_state:
    perm_data = load_permanent_data()
    st.session_state.MEMBER_DATABASE = perm_data["MEMBER_DATABASE"]
    st.session_state.attendance_list = perm_data["attendance_list"]
    st.session_state.match_mode = perm_data["match_mode"]
    
    mode = perm_data["match_mode"]
    quarters = [f"{i}쿼터" for i in range(1, 8 if mode == "2파전" else 10)]
    st.session_state.edited_score_df = pd.DataFrame(perm_data["score_data_dict"], index=quarters)
    st.session_state.current_teams = {}
    st.session_state.initialized = True

# --- 상태 보존용 세션 플래그 생성 ---
if "show_warning" not in st.session_state:
    st.session_state.show_warning = False

# --- 스마트폰 메뉴 구조 정의 ---
menu_1 = "1. 명단 및 팀배분"
menu_2 = "2. 경기 기록실"
menu_3 = "3. 회원별 점수"

st.sidebar.title("MENU")

# --- 관리자 인증 시스템 ---
st.sidebar.markdown("---")
st.sidebar.subheader("관리자 인증")
admin_password = st.sidebar.text_input("비밀번호 입력", type="password")
is_admin = (admin_password == "1234")

if is_admin:
    menu_options = [menu_1, menu_2, menu_3]
else:
    menu_options = [menu_1, menu_2]

page = st.sidebar.radio("메뉴를 선택하세요", menu_options)
st.sidebar.caption("제작자: by홍찬")


# =========================================================================
# ?? 1페이지: 선수 명단 및 팀 배분 기능
# =========================================================================
if page == menu_1:
    st.title("몽말 팀배분 프로그램")
    st.write("오늘 참석한 선수들의 이름을 차례대로 입력하세요. (최대 18명)")
    
    df_attendance = pd.DataFrame({"이름": st.session_state.attendance_list})
    grid_result = st.data_editor(df_attendance, num_rows="fixed", use_container_width=True, hide_index=True)
    
    if grid_result["이름"].tolist() != st.session_state.attendance_list:
        st.session_state.attendance_list = grid_result["이름"].tolist()
        save_permanent_data()
    
    st.markdown("---")
    st.subheader("경기 방식 설정")
    selected_mode = st.radio("오늘 매치 방식을 골라주세요", ["2파전 (8쿼터)", "3파전 (9쿼터)"], index=0 if st.session_state.match_mode == "2파전" else 1)

    # ?? [안전장치 1단계] 팀 짜기 시작 버튼을 누르면 먼저 경고 플래그를 켭니다.
    if st.button("팀 짜기 시작", use_container_width=True, type="primary"):
        st.session_state.show_warning = True

    # ?? [안전장치 2단계] 경고 플래그가 켜졌을 때만 작동하는 확인 폼
    if st.session_state.show_warning:
        st.warning("?? 주의: 팀을 새로 짜면 현재 경기 기록실의 점수가 모두 초기화됩니다. 계속 진행하시겠습니까?")
        
        col1, col2 = st.columns(2)
        with col1:
            # 최종 승인 버튼
            if st.button("네, 새로 짭니다", use_container_width=True, type="secondary"):
                st.session_state.show_warning = False # 플래그 해제
                
                players = []
                for name in st.session_state.attendance_list:
                    cleaned_name = str(name).strip()
                    if cleaned_name and cleaned_name != "None" and cleaned_name != "":
                        if cleaned_name in st.session_state.MEMBER_DATABASE:
                            db_info = st.session_state.MEMBER_DATABASE[cleaned_name]
                            total_score = int(db_info["공격"]) + int(db_info["수비"])
                        else:
                            total_score = 6
                        players.append({"name": cleaned_name, "total": total_score})
                        
                total_players = len(players)
                if total_players < 2:
                    st.error("선수를 입력해 주세요.")
                else:
                    players.sort(key=lambda x: x['total'], reverse=True)
                    
                    new_mode = "2파전" if "2파전" in selected_mode else "3파전"
                    st.session_state.match_mode = new_mode
                    st.session_state.current_teams = {name: [] for name in (["레드", "블루"] if new_mode == "2파전" else ["블랙", "레드", "블루"])}
                    
                    if new_mode == "2파전":
                        for idx, p in enumerate(players):
                            st.session_state.current_teams["레드" if idx % 2 == 0 else "블루"].append(p)
                    else:
                        order = [0, 1, 2]
                        for idx, p in enumerate(players):
                            if idx % 3 == 0 and idx > 0: random.shuffle(order)
                            st.session_state.current_teams[(["블랙", "레드", "블루"])[order[idx % 3]]].append(p)
                    
                    # ?? 확정 시 스코어보드를 완전히 새로 리셋합니다.
                    st.session_state.edited_score_df = get_blank_score_df(new_mode)
                    save_permanent_data()
                    st.rerun()
                    
        with col2:
            # 취소 버튼
            if st.button("아니오, 취소합니다", use_container_width=True):
                st.session_state.show_warning = False
                st.info("팀 짜기가 취소되었습니다. 기존 경기 기록은 무사합니다.")
                st.rerun()

    # 팀 짜기 최종 결과 출력 구역
    if st.session_state.current_teams and not st.session_state.show_warning:
        st.success(f"매칭 완료")
        katalk_text = f"[풋살 팀 매칭 결과 ({st.session_state.match_mode})]\n"
        for t_name, members in st.session_state.current_teams.items():
            m_names = [p['name'] for p in members]
            katalk_text += f"\n- {t_name}팀 ({len(members)}명)\n  : {', '.join(m_names)}\n"
        st.text_area("꾹 눌러서 복사 후 카톡 공지", value=katalk_text, height=140)

# =========================================================================
# ?? 2페이지: 경기 기록실
# =========================================================================
elif page == menu_2:
    st.title(f"실시간 경기 기록실 ({st.session_state.match_mode})")
    st.write("각 쿼터별 스코어를 입력하세요. 점수를 적은 뒤 엔터를 치거나 다른 셀을 누르면 자동 실시간 저장됩니다.")
    
    grid_score = st.data_editor(st.session_state.edited_score_df, use_container_width=True)
    
    if not grid_score.equals(st.session_state.edited_score_df):
        st.session_state.edited_score_df = grid_score
        save_permanent_data()

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
                t_pairs = ["레드", "ブル"]; scores = [int(red_score), int(blue_score)]
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
    
    if is_admin:
        st.markdown("---")
        if st.button("?? 오늘 경기 스코어판 전체 초기화 (데이터 리셋)", use_container_width=True):
            st.session_state.edited_score_df = get_blank_score_df(st.session_state.match_mode)
            save_permanent_data()
            st.rerun()

# =========================================================================
# ? 3페이지: 회원별 점수 관리실
# =========================================================================
else:
    st.title("3. 회원별 점수 관리실")
    st.write("비공개 도감 구역입니다. 여기에 등록된 회원 점수를 토대로 앞 페이지에서 밸런스 팀 매칭이 진행됩니다.")
    
    new_name = st.text_input("회원 이름 입력").strip()
    new_atk = st.slider("공격 능력치", 1, 5, 3)
    new_dfd = st.slider("수비 능력치", 1, 5, 3)
    new_gk = st.slider("키퍼 능력치", 1, 5, 3)
    
    if st.button("도감에 데이터 저장하기", use_container_width=True, type="primary"):
        if not new_name:
            st.error("이름을 입력해 주세요.")
        else:
            st.session_state.MEMBER_DATABASE[new_name] = {"공격": new_atk, "수비": new_dfd, "키퍼": new_gk}
            save_permanent_data()
            st.success(f"성공! [ {new_name} ] 선수의 실력 데이터가 비공개 저장소에 기록되었습니다.")
            st.rerun()
            
    st.markdown("---")
    st.subheader("현재 등록된 전체 회원별 점수 도감")
    db_list = []
    for name, stats in st.session_state.MEMBER_DATABASE.items():
        db_list.append({"이름": name, "공격점수": stats["공격"], "수비점수": stats["수비"], "키퍼점수": stats["키퍼"]})
    st.dataframe(pd.DataFrame(db_list), use_container_width=True, hide_index=True)