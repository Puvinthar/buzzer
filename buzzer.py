import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import time
from playsound import playsound
from streamlit.components.v1 import html

# Function to initialize Firebase
@st.cache_resource
def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("D:\jupyter\project\Firebase-credentials.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# Ensure collections exist
control_ref = db.collection("control").document("buzzer")
if not control_ref.get().exists:
    control_ref.set({"countdown": False})

history_ref = db.collection("buzzer_history")

# Custom CSS with modern styling
st.markdown("""
    <style>
    :root {
        --primary-color: #4CAF50;
        --secondary-color: #2196F3;
        --background-color: rgba(30, 60, 114, 0.95);
    }

    body {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        color: white;
        font-family: 'Poppins', sans-serif;
    }

    .stApp {
        background: var(--background-color);
    }

    .stButton button {
        background: linear-gradient(135deg, var(--primary-color), #45a049);
        border-radius: 25px;
        font-size: 1.2rem;
        padding: 15px 30px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
    }

    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.5);
    }

    .countdown-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        margin: 2rem 0;
        animation: fadeIn 0.5s ease-in;
    }

    .countdown-item {
        text-align: center;
        padding: 1rem 2rem;
        background: linear-gradient(45deg, var(--secondary-color), #1e88e5);
        border-radius: 15px;
        min-width: 120px;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
    }

    .countdown-number {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(45deg, #fff, #e0e0e0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: pulse 1s infinite;
    }

    .countdown-label {
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.8);
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .buzzer-active {
        animation: buzz 0.5s infinite alternate;
    }

    @keyframes buzz {
        from { transform: translateX(-2px); }
        to { transform: translateX(2px); }
    }

    .success-message {
        font-size: 1.5rem;
        color: var(--primary-color);
        text-align: center;
        padding: 1rem;
        border: 2px solid var(--primary-color);
        border-radius: 10px;
        margin: 1rem 0;
        animation: slideIn 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)

# JavaScript for countdown animations
countdown_js = """
<script>
function updateCountdown(number) {
    const container = document.querySelector('.countdown-container');
    container.innerHTML = `
        <div class="countdown-item">
            <div class="countdown-number">${number}</div>
            <div class="countdown-label">SECONDS</div>
        </div>
    `;
    
    if(number === 0) {
        container.innerHTML = `
            <div class="countdown-item" style="animation: none;">
                <div class="countdown-number">GO!</div>
                <div class="countdown-label">BUZZ NOW!</div>
            </div>
        `;
    }
}
</script>
"""

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Title with animation
st.markdown("<h1 style='text-align: center; animation: fadeIn 1s ease-in;'>Tech Quiz Buzzer 🚀</h1>", unsafe_allow_html=True)

# Authentication logic
if not st.session_state.logged_in:
    # Admin Login
    with st.container():
        st.subheader("Admin Portal")
        admin_user = st.text_input("Admin ID")
        admin_pass = st.text_input("Admin Key", type="password")
        if st.button("Access Control Panel"):
            if admin_user == "admin" and admin_pass == "admin123":
                st.session_state.logged_in = True
                st.session_state.is_admin = True
                st.session_state.username = "admin"
                st.success("Admin authenticated")
            else:
                st.error("Invalid credentials")

    # User Login
    with st.container():
        st.subheader("Participant Access")
        username = st.text_input("Username")
        if st.button("Join Session"):
            if username:
                user_ref = db.collection("users").document(username)
                if user_ref.get().exists:
                    st.error("Username taken")
                else:
                    user_ref.set({"buzzed": False, "timestamp": None})
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Welcome {username}!")
            else:
                st.error("Enter username")

# Admin Panel
if st.session_state.logged_in and st.session_state.is_admin:
    st.header("Control Panel")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(" Start Countdown", use_container_width=True):
            control_ref.update({"countdown": True})
    with col2:
        if st.button("Reset Session", use_container_width=True):
            users = db.collection("users").stream()
            for user in users:
                user.reference.update({"buzzed": False, "timestamp": None})
            control_ref.update({"countdown": False})
    
    # Buzzer History
    st.subheader("Session History")
    history = history_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5).stream()
    for doc in history:
        data = doc.to_dict()
        st.markdown(f"""
            <div style="padding: 1rem; margin: 0.5rem 0; background: rgba(255,255,255,0.1); border-radius: 10px;">
                🕒 {data['timestamp'].strftime('%H:%M:%S')} - 👤 {data['username']}
            </div>
        """, unsafe_allow_html=True)

# Participant Interface
if st.session_state.logged_in and not st.session_state.is_admin:
    st.header(f"Welcome, {st.session_state.username}!")
    
    control_data = control_ref.get().to_dict()
    countdown_active = control_data.get("countdown", False)
    
    if countdown_active:
        html(countdown_js)
        with st.empty():
            st.markdown("""
                <div class="countdown-container">
                    <div class="countdown-item">
                        <div class="countdown-number">3</div>
                        <div class="countdown-label">SECONDS</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            for i in range(3, 0, -1):
                html(f"<script>updateCountdown({i})</script>")
                time.sleep(1)
                playsound("countdown.mp3")
            
            st.markdown("""
                <div class="countdown-container">
                    <div class="countdown-item" style="background: linear-gradient(45deg, #4CAF50, #45a049);">
                        <div class="countdown-number">GO!</div>
                        <div class="countdown-label">BUZZ NOW!</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            playsound("buzzer.mp3")
            control_ref.update({"countdown": False})
            time.sleep(2)
    
    # Buzzer Interface
    with st.container():
        user_ref = db.collection("users").document(st.session_state.username)
        user_data = user_ref.get().to_dict()
        
        if st.button(" Buzz In!", disabled=countdown_active,
                    use_container_width=True, type="primary"):
            if not user_data.get("buzzed"):
                user_ref.update({
                    "buzzed": True,
                    "timestamp": datetime.now()
                })
                history_ref.add({
                    "username": st.session_state.username,
                    "timestamp": datetime.now()
                })
                st.success("Buzz registered!")
            else:
                st.error("Already buzzed!")
        
        # Live Buzzer List
        st.subheader("Live Leaderboard")
        buzzers = db.collection("users").where("buzzed", "==", True).stream()
        buzzer_list = [{
            "username": buzzer.id,
            "timestamp": buzzer.to_dict().get("timestamp")
        } for buzzer in buzzers]
        
        buzzer_list.sort(key=lambda x: x["timestamp"])
        
        for idx, buzzer in enumerate(buzzer_list, 1):
            st.markdown(f"""
                <div style="padding: 1rem; margin: 0.5rem 0; 
                          background: rgba(76, 175, 80, 0.1); 
                          border-radius: 10px;
                          border-left: 4px solid var(--primary-color);
                          animation: fadeIn 0.5s ease-out;">
                    #{idx} 🏆 {buzzer['username']} 
                    <span style="float: right; opacity: 0.8;">
                        {buzzer['timestamp'].strftime('%H:%M:%S')}
                    </span>
                </div>
            """, unsafe_allow_html=True)
