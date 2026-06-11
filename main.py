import streamlit as st
import random
import pandas as pd

# 스마트폰 화면 및 브라우저 타이틀 설정
st.set_page_config(page_title="몽말 팀배분 프로그램 by홍찬", layout="centered")
st.title("? 몽말 팀배분 프로그램")
st.caption("제작자: by홍찬")

# --- 데이터 저장소 설정 (웹 브라우저 세션 유지용) ---
if "match_history" not in st.session_state:
    st.session_state.match_history = {
        "블랙": {"승": 0, "무": 0, "패": 0, "득점": 0, "실점": 0, "골득실": 0, "승점": 0, "경기수": 0},
        "레드": {"승": 0, "무": 0, "패": 0, "득점": 0, "실점": 0, "골득실": 0, "승점": 0, "경기수": 0},
        "블루": {"승": 0, "무": 0, "패": 0, "득점": 0, "실점": 0, "골득실": 0, "승점": 0, "경기수": 0}
    }
if "current_teams" not in st.session_state:
    st.session_state.current_teams = {}

# --- [1] 엑셀식 선수 명단 입력 칸 ---
st.header("?? 1. 참석자 명단 및 능력치 입력")
st.write("진짜 엑셀처럼 칸을 누르고 이름과 점수(1~5)를 입력하세요. (최대 18명)")

# 기본 예시 데이터 5명 포함 총 18개 라인 기본 세팅
default_data = {
    "이름": ["손흥민", "이강인", "황희찬", "김민재", "조현우"] + [""] * 13,
    "공격 (1~5)": [5, 5, 4, 2, 1] + [1] * 13,
    "수비 (1~5)": [4, 3, 3, 5, 2] + [1] * 13,
    "키퍼 (1~5)": [2, 2, 1, 3, 5] + [1] * 13
}
df_init = pd.DataFrame(default_data)

# 스마트폰에서 엑셀처럼 바로 타이핑 가능한 표(Grid) 출력
edited_df = st.data_editor(df_init, num_rows="fixed", use_container_width=True, hide_index=True)

# --- [2] 황금밸런스 팀 매칭 버튼 ---
if st.button("?? 황금밸런스 팀 짜기 시작!", use_container_width=True):
    players = []
    # 표에서 이름이 입력된 사람만 필터링하여 수집
    for _, row in edited_df.iterrows():
        name = str(row["이름"]).strip()
        if name and name != "None" and name != "":
            # ?? [피드백 반영] 키퍼 점수를 완벽히 배제하고 오직 [공격 + 수비] 점수로만 밸런스 정렬!
            try:
                atk_val = int(row["공격 (1~5)"])
                dfd_val = int(row["수비 (1~5)"])
                players.append({"name": name, "total": atk_val + dfd_val})
            except:
                continue
            
    total_players = len(players)
    if total_players < 2:
        st.error("? 최소 2명 이상의 선수 이름을 엑셀 칸에 입력해 주세요.")
    else:
        # 순수 필드 전력 기준 정렬 후 지그재그 분배
        players.sort(key=lambda x: x['total'], reverse=True)
        
        if total_players < 15:
            team_names = ["레드", "블루"]
            st.session_state.current_teams = {name: [] for name in team_names}
            for idx, p in enumerate(players):
                st.session_state.current_teams["레드" if idx % 2 == 0 else "블루"].append(p)
        else:
            team_names = ["블랙", "레드", "블루"]
            st.session_state.current_teams = {name: [] for name in team_names}
            order = [0, 1, 2]
            for idx, p in enumerate(players):
                if idx % 3 == 0 and idx > 0:
                    random.shuffle(order)
                st.session_state.current_teams[team_names[order[idx % 3]]].append(p)

# --- [3] 매칭 결과 및 카톡 복사용 텍스트 창 ---
if st.session_state.current_teams:
    st.success("? 팀 매칭이 완료되었습니다!")
    
    # 카톡 포맷 생성
    katalk_text = f"?? [이번 주 풋살 팀 매칭 결과 (총 {len(st.session_state.current_teams.values())}개 팀)]\n"
    katalk_text += "===========================\n"
    
    for t_name, members in st.session_state.current_teams.items():
        m_names = [p['name'] for p in members]
        katalk_text += f"\n■ {t_name}팀 ({len(members)}명)\n   - {', '.join(m_names)}\n"
    katalk_text += "\n==========================="
    
    st.text_area("?? 꾹 눌러서 복사한 뒤 카톡방에 공지하세요", value=katalk_text, height=180)

# --- [4] 모바일 9쿼터 기록실 & 골득실 순위표 ---
st.divider()
st.header("?? 2. 실시간 1~9쿼터 경기 기록실")
st.write("쿼터가 끝날 때마다 점수를 적으세요. 승점(승3/무1/패0), 골득실, 다득점 순으로 순위가 매겨집니다.")

# 3개 열로 나누어 모바일 화면에서 바둑판 배열로 깔끔하게 배치
q_inputs = []
cols = st.columns(3)
for i in range(9):
    with cols[i % 3]:
        st.write(f"**{i+1}쿼터(Q)**")
        # 기본 대진 매칭 텍스트 자동 가이드
        t1 = st.text_input(f"{i+1}Q 팀1", "레드" if i%3==0 else ("블랙" if i%3==1 else "블루"), key=f"t1_{i}")
        s1 = st.number_input(f"{i+1}Q 점수1", min_value=0, value=0, key=f"s1_{i}")
        st.write("vs")
        s2 = st.number_input(f"{i+1}Q 점수2", min_value=0, value=0, key=f"s2_{i}")
        t2 = st.text_input(f"{i+1}Q 팀2", "블루" if i%3==0 else ("레드" if i%3==1 else "블랙"), key=f"t2_{i}")
        q_inputs.append({"t1": t1, "s1": s1, "s2": s2, "t2": t2})
        st.write("---")

# 정산 버튼 누를 때 연산 시작
if st.button("?? 1~9쿼터 스코어 반영 및 최종 순위 계산", use_container_width=True, type="primary"):
    # 전적 데이터 초기화 (다시 누적 연산할 때 수치 뻥튀기 방지)
    history = {t: {"승": 0, "무": 0, "패": 0, "득점": 0, "실점": 0, "골득실": 0, "승점": 0, "경기수": 0} for t in ["블랙", "레드", "블루"]}
    
    for q in q_inputs:
        team1, score1, score2, team2 = q["t1"].strip(), int(q["s1"]), int(q["s2"]), q["t2"].strip()
        if team1 not in history or team2 not in history:
            continue
            
        history[team1]["경기수"] += 1
        history[team2]["경기수"] += 1
        history[team1]["득점"] += score1; history[team1]["실점"] += score2
        history[team2]["득점"] += score2; history[team2]["실점"] += score1
        
        # 정식 승점 룰 대입 (승3, 무1, 패0)
        if score1 > score2:
            history[team1]["승"] += 1; history[team1]["승점"] += 3
            history[team2]["패"] += 1
        elif score1 < score2:
            history[team2]["승"] += 1; history[team2]["승점"] += 3
            history[team1]["패"] += 1
        else:
            history[team1]["무"] += 1; history[team1]["승점"] += 1
            history[team2]["무"] += 1; history[team2]["승점"] += 1
            
    # 골득실 최종 마감
    for t in history:
        history[t]["골득실"] = history[t]["득점"] - history[t]["실점"]
        
    st.session_state.match_history = history

# ?? 실시간 최종 순위표 UI 그리기
st.subheader("?? 오늘 경기 실시간 순위표")
rank_data = []
for t_name, stat in st.session_state.match_history.items():
    rank_data.append({
        "팀": t_name, "승점": stat["승점"], "골득실": stat["골득실"], "득점(다득점)": stat["득점"],
        "전적": f"{stat['경기수']}전 {stat['승']}승 {stat['무']}무 {stat['패']}패"
    })
df_rank = pd.DataFrame(rank_data)

# 중요: 승점 차순 -> 골득실 차순 -> 다득점 차순 순서로 정교하게 소팅
df_rank = df_rank.sort_values(by=["승점", "골득실", "득점(다득점)"], ascending=[False, False, False]).reset_index(drop=True)
df_rank.index = df_rank.index + 1 # 인덱스 1등부터 표기
st.dataframe(df_rank, use_container_width=True)