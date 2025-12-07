import streamlit as st
import pandas as pd
from datetime import datetime, timedelta  # timedelta 추가!
import streamlit.components.v1 as components

st.set_page_config(page_title="세탁기 예약", page_icon="🧺", layout="wide")

st.title("🧺 세탁기 스마트 예약 시스템")

# CSV 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_csv('laundry_example.csv', header=0, skiprows=[1, 2])
    df.columns = df.columns.str.strip()
    df['hour'] = df['hour'].astype(int)
    return df

df = load_data()

# 현재 시간
now = datetime.now()
current_hour = now.hour

col1, col2 = st.columns([1, 2])

with col1:
    st.info(f"🕐 **현재**: {current_hour}시 {now.minute:02d}분")
    use_when = st.radio("언제 사용?", 
                        ["지금 바로", "1시간 후", "3시간 후", "6시간 후", "8시간 후"])

# 시간별 평균 혼잡도 계산
hourly_congestion = {}
service_hours = list(range(7, 24))

for hour in service_hours:
    hour_data = df[df['hour'] == hour]
    if len(hour_data) > 0:
        avg_usage = hour_data['usage_count'].mean()
        congestion_score = 0
        for idx, row in hour_data.iterrows():
            cong = row['congestion']
            if cong == 'low':
                congestion_score += 0
            elif cong == 'medium':
                congestion_score += 25
            elif cong == 'high':
                congestion_score += 50
            elif cong == 'very_high':
                congestion_score += 75
        
        avg_congestion = congestion_score / len(hour_data)
        hourly_congestion[hour] = int(avg_congestion)

time_map = {"지금 바로": 0, "1시간 후": 1, "3시간 후": 3, "6시간 후": 6, "8시간 후": 8}
target_hour = (current_hour + time_map[use_when]) % 24

with col2:
    # 서비스 시간 체크
    if target_hour >= 23 or target_hour < 7:
        st.warning("⚠️ **23시부터 7시까지는 사용시간이 아닙니다!**")
        st.info("🕐 **서비스 이용시간**: 오전 7시 ~ 오후 11시 (23시)")
        
        if target_hour >= 22:
            next_open = 7
            wait_hours = (24 - target_hour) + next_open
        else:
            next_open = 7
            wait_hours = next_open - target_hour
        
        st.success(f"💡 **다음 운영 시작**: 오전 7시 (약 {wait_hours}시간 후)")
        
    elif target_hour not in hourly_congestion:
        st.warning("⚠️ 해당 시간대 데이터가 없습니다")
    else:
        target_cong = hourly_congestion[target_hour]
        
        if target_cong < 40:
            st.success(f"### ✅ {use_when} 사용하세요!")
            st.markdown(f"**시간**: {target_hour}시")
            
            cols = st.columns(3)
            cols[0].metric("혼잡도", f"{target_cong}%")
            cols[1].metric("대기시간", "약 0분")
            cols[2].metric("상태", "😊 쾌적")
            
            if target_cong < 20:
                st.balloons()
        else:
            st.error(f"### ⚠️ {use_when}은 혼잡해요")
            st.markdown(f"**시간**: {target_hour}시 (혼잡도 {target_cong}%)")
            
            best_hour = min(hourly_congestion.items(), key=lambda x: x[1])
            st.success(f"### 💡 추천: {best_hour[0]}시")
            st.markdown(f"**혼잡도**: {best_hour[1]}% - 훨씬 쾌적해요!")

# 50분 알람 섹션
st.divider()
st.subheader("⏰ 세탁 완료 알람")

# 알람 시간 계산
alarm_time = datetime.now() + timedelta(minutes=50)
alarm_hour = alarm_time.hour
alarm_minute = alarm_time.minute

# JavaScript로 플랫폼 감지 및 알람 설정
alarm_component = f"""
<script>
function setPhoneAlarm() {{
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    const hour = {alarm_hour};
    const minute = {alarm_minute};
    
    // Android 감지
    if (/android/i.test(userAgent)) {{
        // Android 알람 인텐트
        const androidUrl = `intent://alarm#Intent;scheme=alarm;action=android.intent.action.SET_ALARM;i.android.intent.extra.alarm.HOUR=${{hour}};i.android.intent.extra.alarm.MINUTES=${{minute}};S.android.intent.extra.alarm.MESSAGE=세탁완료!;end`;
        window.location.href = androidUrl;
    }}
    // iOS 감지
    else if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {{
        alert('시계 앱을 열어 ' + hour + '시 ' + minute + '분 알람을 설정해주세요!');
        // iOS 시계 앱 열기 시도
        setTimeout(() => {{
            window.location.href = 'clock-alarm://';
        }}, 100);
    }}
    // PC나 기타 기기
    else {{
        alert('모바일 기기에서 이용해주세요!\\n\\nPC에서는 브라우저 알림을 사용하세요.');
    }}
}}

// 웹 알림 (백업용)
function setWebNotification() {{
    if (!("Notification" in window)) {{
        alert("이 브라우저는 알림을 지원하지 않습니다.");
        return;
    }}
    
    Notification.requestPermission().then(permission => {{
        if (permission === "granted") {{
            alert("✅ 브라우저 알림이 설정되었습니다!\\n50분 후에 알림이 울립니다.");
            
            // 50분 = 3,000,000ms
            setTimeout(() => {{
                new Notification("🧺 세탁 완료!", {{
                    body: "세탁기를 확인하세요!",
                    requireInteraction: true,
                    tag: 'laundry-alarm'
                }});
                
                // 알림음 재생
                try {{
                    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBzKH0fPTgjMGHm7A7+OZUREOVKXX8bllHAU+lt7xwHMoByJ+zPLaizsIGGS57OihUhELTKXm8LdnHgU7k9ry0H4sBSJ7yvLajTsIF2W57OmiUhIMTKTl8LhnHgY8lNvyz4IrBSF6y/LajjwJGGS56+mjUxINTKXl8LhnHwU7lNry0H8sBSF7y/LbjjwJGGO46+mjUxINTKXl8LhnHwU7lNvy0H8sBSF7y/LbjjwJGGO46+mjUxINTKXl8LhnHwU7lNvy0H8sBSF7y/LbjjwJGGO46+mjUxINTKXl8LhnHwU7lNvy0H8sBSF7y/LbjjwJGGO46+mjUxINTKXl8LhnHwU7lNvy0H8sBSF7y/LbjjwJGGO46+mjUxINTKXl8LhnHwU7lNvy0H8sBSF7y/LbjjwJGGO46+mjUxINTKXl8LhnHwU7lNvy0H8sBSF7y/LbjjwJGGO46+mjUxINTKXl8LhnHwU7lNvy0H8sBSF7y/LbjjwJGGO46+mjUxINTKXl8LhnHwU7lNvy0H8sBSF7y/LbjjwJGGO46+mjUxINTKXl8LhnHwU7lNvy0H8sBSF7y/Lb');
                    audio.play();
                }} catch(e) {{
                    console.log('Audio playback failed:', e);
                }}
            }}, 3000000);
        }} else {{
            alert("❌ 알림 권한이 거부되었습니다.\\n브라우저 설정에서 알림을 허용해주세요.");
        }}
    }});
}}
</script>

<style>
.alarm-btn {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px 40px;
    font-size: 18px;
    font-weight: bold;
    border: none;
    border-radius: 15px;
    cursor: pointer;
    width: 100%;
    margin: 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    transition: all 0.3s;
}}
.alarm-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}}
.alarm-btn:active {{
    transform: translateY(0);
}}
.web-alarm-btn {{
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}}
</style>

<div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 15px;">
    <h3 style="margin-bottom: 20px;">🔔 알람 시간: {alarm_hour:02d}시 {alarm_minute:02d}분</h3>
    
    <button onclick="setPhoneAlarm()" class="alarm-btn">
        📱 핸드폰 알람 설정 (50분 후)
    </button>
    
    <button onclick="setWebNotification()" class="alarm-btn web-alarm-btn">
        🌐 브라우저 알림 설정 (백업용)
    </button>
    
    <p style="color: #666; margin-top: 20px; font-size: 14px;">
        💡 <strong>Android</strong>: 알람 앱이 자동으로 열립니다<br>
        💡 <strong>iPhone</strong>: 시계 앱에서 수동으로 설정해주세요<br>
        💡 <strong>PC</strong>: 브라우저 알림을 사용하세요
    </p>
</div>
"""

# 컴포넌트 렌더링
components.html(alarm_component, height=350)

# 전체 현황
st.divider()
st.subheader("📊 시간대별 혼잡도 (7시~23시)")

if hourly_congestion:
    all_hours = list(range(7, 24))
    chart_data = pd.DataFrame({
        '혼잡도': [hourly_congestion.get(h, 0) for h in all_hours]
    }, index=all_hours)

    st.bar_chart(chart_data)
else:
    st.warning("시간대별 데이터가 없습니다.")

# 주요 시간대 요약
st.subheader("⏰ 주요 시간대 정보")
cols = st.columns(4)

key_hours = [
    (7, 9, "아침"),
    (12, 14, "점심"),
    (18, 20, "저녁"),
    (21, 21, "마감 전")
]

for i, (start, end, label) in enumerate(key_hours):
    hours_in_range = [h for h in range(start, end+1) if h in hourly_congestion]
    if hours_in_range:
        avg_cong = sum(hourly_congestion[h] for h in hours_in_range) // len(hours_in_range)
    else:
        avg_cong = 0
    
    with cols[i]:
        if avg_cong < 30:
            st.success(f"**{label} ({start}~{end}시)**")
            emoji = "🟢"
            status = "쾌적"
        elif avg_cong < 60:
            st.warning(f"**{label} ({start}~{end}시)**")
            emoji = "🟡"
            status = "보통"
        else:
            st.error(f"**{label} ({start}~{end}시)**")
            emoji = "🔴"
            status = "혼잡"
        
        st.metric(status, f"{avg_cong}%")
        st.write(f"{emoji}")

st.caption("⏰ **서비스 운영시간**: 오전 7시 ~ 오후 9시 (21시)")
st.caption("💤 **운영 종료**: 오후 10시 (22시) ~ 오전 6시")