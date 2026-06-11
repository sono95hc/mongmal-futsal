import streamlit as st
import random
import pandas as pd
import json
import os

# 스마트폰 화면 및 브라우저 타이틀 설정
st.set_page_config(page_title="몽말 팀배분 프로그램 by홍찬", layout="centered")

# --- [파일 영구 저장 엔진] 시스템 설정 ---
DB_FILE = "futsal_data.json"

# 초기 데이터 구조 정의 (빈칸으로 세팅)
def get_blank_score_df(mode="3파전"):
    if mode == "2파전":
        quarters = [f"{i}쿼터" for i in range(1, 9)]
        return pd.DataFrame({"블루": [None] * 8, "레드": [None] * 8}, index=quarters)
    else:
        quarters = [f"{i}쿼터" for i in range(1, 10)]
        return pd.DataFrame({"블루": [None] * 9, "블랙": [None] * 9, "레드": [None] * 9}, index=quarters)

# 1. 파일에서 데이터 읽어오기 함수
def load_permanent_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "MEMBER_DATABASE" not in data:
                    data["MEMBER_DATABASE"] = {
                        "손흥민": {"공격": 5.0, "수비": 4.0, "키퍼": 2.0},
                        "이강인": {"공격": 5.0, "수비": 3.0, "키퍼": 2.0},
                        "황희찬": {"공격": 4.0, "수비": 3.0, "키퍼": 1.0},
                        "김민재": {"공격": 2.0, "수비": 5.0, "키퍼": 3.0},
                        "조현우": {"공격": 1.0, "수비": 2.0, "키퍼": 5.0}
                    }
                return data
        except:
            pass
    
    return {
        "MEMBER_DATABASE": {
            "손흥민": {"공격": 5.0, "수비": 4.0, "키퍼": 2.0},
            "이강인": {"공격": 5.0, "수비": 3.0, "키퍼": 2.0},
            "황희찬": {"공격": 4.0, "수비": 3.0, "키퍼": 1.0},
            "김민재": {"공격": 2.0, "수비": 5.0, "키퍼": 3.0},
            "조현우": {"공격": 1.0, "수비": 2.0, "키퍼": 5.0}
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
    
    raw_scores = perm_data["score_data_dict"]
    st.session_state.edited_score_df = pd.DataFrame(raw_scores, index=quarters)
    st.session_state.current_teams = {}
    st.session_state.initialized = True

# 3페이지 대량 입력용 표 초기화
if "bulk_input_df" not in st.session_state:
    st.session_state.bulk_input_df = pd.DataFrame({
        "이름": [""] * 15, "공격": [3.0] * 15, "수비": [3.0] * 15, "키퍼": [3.0] * 15
    })

if "show_warning" not in st.session_state:
    st.session_state.show_warning = False

# 메뉴 구조 정의
menu_1 = "1. 명단 및 팀배분"
menu_2 = "2. 경기 기록실"
menu_3 = "3. 회원별 점수"

st.sidebar.title("MENU")

# 관리자 인증
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
# 1페이지: 선수 명단 및 팀 배분 기능
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

    if st.button("팀 짜기 시작", use_container_width=True, type="primary"):
        st.session_state.show_warning = True

    if st.session_state.show_warning:
        st.warning("주의: 팀을 새로 짜면 현재 경기 기록실의 점수가 모두 초기화됩니다. 계속 진행하시겠습니까?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("네, 새로 짭니다", use_container_width=True, type="secondary"):
                st.session_state.show_warning = False
                
                players = []
                for name in st.session_state.attendance_list:
                    cleaned_name = str(name).strip()
                    if cleaned_name and cleaned_name != "None" and cleaned_name != "":
                        if cleaned_name in st.session_state.MEMBER_DATABASE:
                            db_info = st.session_state.MEMBER_DATABASE[cleaned_name]
                            total_score = float(db_info["공격"]) + float(db_info["수비"])
                        else:
                            total_score = 6.0
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
                    
                    st.session_state.edited_score_df = get_blank_score_df(new_mode)
                    save_permanent_data()
                    st.rerun()
                    
        with col2:
            if st.button("아니오, 취소합니다", use_container_width=True):
                st.session_state.show_warning = False
                st.info("팀 짜기가 취소되었습니다. 기존 경기 기록은 무사합니다.")
                st.rerun()

    if st.session_state.current_teams and not st.session_state.show_warning:
        st.success("매칭 완료")
        
        katalk_text = f"[풋살 팀 매칭 결과 ({st.session_state.match_mode})]\n"
        for t_name, members in st.session_state.current_teams.items():
            m_names = [p['name'] for p in members]
            random.shuffle(m_names) 
            katalk_text += f"\n{t_name}팀 ({len(members)}명)\n{', '.join(m_names)}\n"
            
        st.text_area("꾹 눌러서 복사 후 카톡 공지", value=katalk_text, height=140)

# =========================================================================
# 2페이지: 경기 기록실 (★ black -> 블랙 오타 전면 수정 완료)
# =========================================================================
elif page == menu_2:
    st.title(f"실시간 경기 기록실 ({st.session_state.match_mode})")
    
    st.subheader("쿼터 스코어 입력창")
    st.write("경기가 끝난 쿼터를 고르고, 시합을 뛴 두 팀을 선택해 점수를 입력하세요.")
    
    loop_count = 8 if st.session_state.match_mode == "2파전" else 9
    quarter_options = [f"{i}쿼터" for i in range(1, loop_count + 1)]
    
    selected_q = st.selectbox("기록할 쿼터 선택", quarter_options)
    current_q_data = st.session_state.edited_score_df.loc[selected_q]
    
    if st.session_state.match_mode == "3파전":
        default_match_idx = 0
        if pd.notna(current_q_data["블루"]) and pd.notna(current_q_data["레드"]) and pd.isna(current_q_data["블랙"]):
            default_match_idx = 0
        elif pd.notna(current_q_data["블루"]) and pd.notna(current_q_data["블랙"]) and pd.isna(current_q_data["레드"]):
            default_match_idx = 1
        elif pd.notna(current_q_data["블랙"]) and pd.notna(current_q_data["레드"]) and pd.isna(current_q_data["블루"]):
            default_match_idx = 2
            
        match_type = st.radio("이번 쿼터 경기 대진", ["블루 vs 레드", "블루 vs 블랙", "블랙 vs 레드"], index=default_match_idx)
        
        c1, c2 = st.columns(2)
        if match_type == "블루 vs 레드":
            with c1: val_blue = st.number_input("블루 점수", min_value=0, max_value=99, value=int(current_q_data["블루"]) if pd.notna(current_q_data["블루"]) else 0, step=1)
            with c2: val_red = st.number_input("레드 점수", min_value=0, max_value=99, value=int(current_q_data["레드"]) if pd.notna(current_q_data["레드"]) else 0, step=1)
            val_black = None
        elif match_type == "블루 vs 블랙":
            with c1: val_blue = st.number_input("블루 점수", min_value=0, max_value=99, value=int(current_q_data["블루"]) if pd.notna(current_q_data["블루"]) else 0, step=1)
            # ?? [버그 수정 포인트] 아래 "black" 오타를 "블랙"으로 완벽히 교체했습니다.
            with c2: val_black = st.number_input("블랙 점수", min_value=0, max_value=99, value=int(current_q_data["블랙"]) if pd.notna(current_q_data["블랙"]) else 0, step=1)
            val_red = None
        else:
            with c1: val_black = st.number_input("블랙 점수", min_value=0, max_value=99, value=int(current_q_data["블랙"]) if pd.notna(current_q_data["블랙"]) else 0, step=1)
            with c2: val_red = st.number_input("레드 점수", min_value=0, max_value=99, value=int(current_q_data["레드"]) if pd.notna(current_q_data["레드"]) else 0, step=1)
            val_blue = None
            
    else:
        c1, c2 = st.columns(2)
        with c1: val_blue = st.number_input("블루 점수", min_value=0, max_value=99, value=int(current_q_data["블루"]) if pd.notna(current_q_data["블루"]) else 0, step=1)
        with c2: val_red = st.number_input("레드 점수", min_value=0, max_value=99, value=int(current_q_data["레드"]) if pd.notna(current_q_data["레드"]) else 0, step=1)
        val_black = None

    if st.button("해당 쿼터 점수 저장하기", use_container_width=True, type="primary"):
        st.session_state.edited_score_df.at[selected_q, "블루"] = val_blue
        st.session_state.edited_score_df.at[selected_q, "레드"] = val_red
        if st.session_state.match_mode == "3파전":
            st.session_state.edited_score_df.at[selected_q, "블랙"] = val_black
            
        save_permanent_data()
        st.success(f"{selected_q} 점수가 성공적으로 저장되었습니다!")
        st.rerun()

    st.markdown("---")
    st.subheader("현재까지 기록된 쿼터 현황판")
    
    display_score_df = st.session_state.edited_score_df.copy()
    display_score_df = display_score_df.fillna("-")
    st.dataframe(display_score_df, use_container_width=True)

    # --- 전적 계산 엔진 ---
    history_keys = ["레드", "블루"] if st.session_state.match_mode == "2파전" else ["레드", "블랙", "블루"]
    history = {t: {"W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "GD": 0, "PTS": 0, "MP": 0} for t in history_keys}

    for i in range(loop_count):
        b_val = st.session_state.edited_score_df.iloc[i]["블루"]
        r_val = st.session_state.edited_score_df.iloc[i]["레드"]
        bl_val = st.session_state.edited_score_df.iloc[i]["블랙"] if st.session_state.match_mode == "3파전" else None
        
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
    
    if is_admin:
        st.markdown("---")
        if st.button("오늘 경기 스코어판 전체 초기화 (데이터 리셋)", use_container_width=True):
            st.session_state.edited_score_df = get_blank_score_df(st.session_state.match_mode)
            save_permanent_data()
            st.rerun()

# =========================================================================
# 3페이지: 회원별 점수 관리실
# =========================================================================
else:
    st.title("3. 회원별 점수 관리실")
    
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
            st.success(f"성공! 총 {saved_count}명의 데이터가 도감에 등록되었습니다.")
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
            st.success("도감의 수정/삭제 변경사항이 장부에 영구 저장되었습니다!")
            st.rerun()