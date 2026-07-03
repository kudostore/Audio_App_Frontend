import streamlit as st
import requests
import json
import time

# ── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="AudioSlice AI",
    page_icon="🎵",
    layout="centered"
)

# ── Custom CSS ───────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }

    /* Cards */
    .slice-card {
        background: #1a1a2e;
        border: 1px solid #16213e;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
    }

    /* Title styling */
    h1 {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
        border: none !important;
        color: white !important;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #b6bbff !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        color: white !important;
    }

    /* Progress bar */
    .stage-bar {
        display: flex;
        justify-content: space-between;
        margin: 10px 0 20px 0;
        padding: 10px;
        background: #1a1a2e;
        border-radius: 10px;
    }

    .stage-item {
        text-align: center;
        font-size: 12px;
        color: #888;
    }

    .stage-item.active {
        color: #667eea;
        font-weight: bold;
    }

    .stage-item.done {
        color: #4CAF50;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Constants ────────────────────────────────────────────
API_URL = "https://audioapp-production.up.railway.app"

PUNCTUATION_LABELS = {
    '.':  'Period ( . )',
    '!':  'Exclamation ( ! )',
    '?':  'Question Mark ( ? )',
    ',':  'Comma ( , )',
    ';':  'Semicolon ( ; )',
    ':':  'Colon ( : )',
    '।':  'Purna Viram ( । )',
}

LANGUAGE_OPTIONS = {
    "Hindi":    "hi",
    "English":  "en",
    "Marathi":  "mr",
    "Gujarati": "gu",
    "Bengali":  "bn"
}

# ── Helper Functions ─────────────────────────────────────
def save_login(token, name):
    st.query_params["token"] = token
    st.query_params["name"] = name

def load_login():
    token = st.query_params.get("token", None)
    name = st.query_params.get("name", None)
    return token, name

def clear_login():
    st.query_params.clear()

def show_stage_bar(current_stage):
    stages = ["Upload", "Review", "Final", "BGM"]
    stage_map = {1: 0, 3: 1, 4: 2, 5: 3, 6: 3}
    current_idx = stage_map.get(current_stage, 0)

    cols = st.columns(len(stages))
    for i, (col, stage) in enumerate(zip(cols, stages)):
        with col:
            if i < current_idx:
                st.markdown(f"<div style='text-align:center; color:#4CAF50; font-size:13px'>✅ {stage}</div>", unsafe_allow_html=True)
            elif i == current_idx:
                st.markdown(f"<div style='text-align:center; color:#667eea; font-weight:bold; font-size:13px'>● {stage}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center; color:#555; font-size:13px'>○ {stage}</div>", unsafe_allow_html=True)
    st.markdown("---")

def api_post(url, **kwargs):
    """Safe API call with proper error handling."""
    try:
        response = requests.post(url, **kwargs)
        return response, None
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot connect to server. Make sure FastAPI is running."
    except requests.exceptions.Timeout:
        return None, "⏱️ Request timed out. Please try again."
    except Exception as e:
        return None, f"❌ Unexpected error: {str(e)}"

def api_get(url, **kwargs):
    """Safe GET API call."""
    try:
        response = requests.get(url, **kwargs)
        return response, None
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot connect to server."
    except requests.exceptions.Timeout:
        return None, "⏱️ Request timed out."
    except Exception as e:
        return None, f"❌ Error: {str(e)}"

def api_delete(url, **kwargs):
    """Safe DELETE API call."""
    try:
        requests.delete(url, **kwargs)
    except:
        pass  # Silent fail for delete

# ── Session State Init ───────────────────────────────────
defaults = {
    "token": None,
    "user_name": None,
    "auth_page": "login",
    "stage": 1,
    "session_id": None,
    "slices": [],
    "final_audio": None,
    "final_audio_path": None,
    "bgm_audio": None
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Auto login ───────────────────────────────────────────
if st.session_state.token is None:
    saved_token, saved_name = load_login()
    if saved_token:
        st.session_state.token = saved_token
        st.session_state.user_name = saved_name


# ════════════════════════════════════════════════════════
# AUTH PAGES
# ════════════════════════════════════════════════════════
if st.session_state.token is None:

    st.markdown("<br>", unsafe_allow_html=True)
    st.title("🎵 AudioSlice AI")
    st.markdown("<p style='color:#888; margin-top:-10px'>Slice your Hindi audio with AI precision</p>", unsafe_allow_html=True)
    st.markdown("---")

    # ── LOGIN ────────────────────────────────────────────
    if st.session_state.auth_page == "login":

        st.subheader("🔐 Welcome Back")

        email = st.text_input(
            "Email Address",
            placeholder="you@gmail.com",
            key="login_email"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Login →", use_container_width=True, type="primary"):
            if not email.strip():
                st.error("Please enter your email!")
            elif not password.strip():
                st.error("Please enter your password!")
            else:
                with st.spinner("Logging in..."):
                    response, error = api_post(
                        f"{API_URL}/login",
                        data={"email": email, "password": password}
                    )
                    if error:
                        st.error(error)
                    elif response.status_code == 200:
                        data = response.json()
                        if data["success"]:
                            st.session_state.token = data["token"]
                            st.session_state.user_name = data["name"]
                            save_login(data["token"], data["name"])
                            st.rerun()
                        else:
                            st.error(f"❌ {data['message']}")

        st.markdown("---")
        st.markdown("<p style='text-align:center; color:#888'>Don't have an account?</p>", unsafe_allow_html=True)
        if st.button("Create Free Account", use_container_width=True):
            st.session_state.auth_page = "register"
            st.rerun()

    # ── REGISTER ─────────────────────────────────────────
    elif st.session_state.auth_page == "register":

        st.subheader("📝 Create Account")

        name = st.text_input("Full Name", placeholder="Rahul Sharma", key="reg_name")
        email = st.text_input("Email Address", placeholder="you@gmail.com", key="reg_email")
        password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Create Account →", use_container_width=True, type="primary"):
            if not name.strip():
                st.error("Please enter your name!")
            elif not email.strip():
                st.error("Please enter your email!")
            elif not password.strip():
                st.error("Please enter your password!")
            elif password != confirm_password:
                st.error("Passwords don't match!")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters!")
            else:
                with st.spinner("Creating account..."):
                    response, error = api_post(
                        f"{API_URL}/register",
                        data={"name": name, "email": email, "password": password}
                    )
                    if error:
                        st.error(error)
                    elif response.status_code == 200:
                        data = response.json()
                        if data["success"]:
                            st.success("✅ Account created! Please login.")
                            st.session_state.auth_page = "login"
                            st.rerun()
                        else:
                            st.error(f"❌ {data['message']}")

        st.markdown("---")
        st.markdown("<p style='text-align:center; color:#888'>Already have an account?</p>", unsafe_allow_html=True)
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()


# ════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════
else:

    # ── Top Bar ──────────────────────────────────────────
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"<p style='color:#888; padding-top:8px'>👋 Welcome, <b style='color:white'>{st.session_state.user_name}</b></p>", unsafe_allow_html=True)
    with col2:
        if st.button("Logout", type="secondary"):
            for key in ["token", "user_name", "stage", "slices",
                       "session_id", "final_audio", "final_audio_path", "bgm_audio"]:
                st.session_state[key] = None if key not in ["slices"] else []
            st.session_state.stage = 1
            clear_login()
            st.rerun()

    # ── Stage Progress Bar ───────────────────────────────
    show_stage_bar(st.session_state.stage)

    # ════════════════════════════════════════════════════
    # STAGE 1 — UPLOAD
    # ════════════════════════════════════════════════════
    if st.session_state.stage == 1:

        st.title("🎵 AudioSlice AI")
        st.markdown("<p style='color:#888'>Upload your audio and script to slice it automatically with AI</p>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Upload section
        audio_file = st.file_uploader(
            "📁 Upload Audio File (MP3, WAV, M4A — max 50MB)",
            type=["mp3", "wav", "m4a"]
        )

        original_text = st.text_area(
            "📝 Paste Your Original Script",
            height=180,
            placeholder="नमस्कार! आज के meditation session में आपका स्वागत है। इस meditation से आपकी दिन भर की थकान दूर होगी।"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🌐 Language**")
            selected_language_name = st.selectbox(
                "Language",
                options=list(LANGUAGE_OPTIONS.keys()),
                index=0,
                label_visibility="collapsed"
            )
            selected_language_code = LANGUAGE_OPTIONS[selected_language_name]

        with col2:
            st.markdown("**✂️ Slice At Punctuation**")
            all_punctuation = ['.', '!', '?', ',', ';', ':', '।']
            default_selected = ['.', '!', '?', ',', '।']
            selected_punctuation = []

            punct_cols = st.columns(4)
            for i, punct in enumerate(all_punctuation):
                with punct_cols[i % 4]:
                    if st.checkbox(
                        PUNCTUATION_LABELS[punct].split('(')[0].strip(),
                        value=punct in default_selected,
                        key=f"punct_{punct}"
                    ):
                        selected_punctuation.append(punct)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🔪 Slice Audio with AI", use_container_width=True, type="primary"):
            if audio_file is None:
                st.error("📁 Please upload an audio file!")
            elif not original_text.strip():
                st.error("📝 Please paste your Hindi script!")
            elif len(selected_punctuation) == 0:
                st.error("✂️ Please select at least one punctuation mark!")
            else:
                with st.spinner(f"🤖 AI is transcribing your {selected_language_name} audio... this may take 1-2 minutes ⏳"):
                    response, error = api_post(
                        f"{API_URL}/slice",
                        files={"audio": (audio_file.name, audio_file, "audio/mpeg")},
                        data={
                            "original_text": original_text,
                            "language": selected_language_code,
                            "punctuation_list": json.dumps(selected_punctuation)
                        },
                        timeout=900
                    )

                    if error:
                        st.error(error)
                        st.info("💡 Make sure your FastAPI server is running: `uvicorn main:app --reload`")
                    elif response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            st.session_state.session_id = data["session_id"]
                            st.session_state.slices = data["slices"]
                            st.session_state.stage = 3
                            st.rerun()
                        else:
                            st.error(f"❌ {data.get('error', 'Something went wrong!')}")
                    else:
                        st.error(f"❌ Server error: {response.status_code}")

    # ════════════════════════════════════════════════════
    # STAGE 3 — REVIEW SLICES
    # ════════════════════════════════════════════════════
    elif st.session_state.stage == 3:

        st.title("✂️ Review Slices")
        st.markdown("<p style='color:#888'>Play each slice, set pauses, delete unwanted parts</p>", unsafe_allow_html=True)
        st.warning("⚠️ Don't refresh — you'll lose your progress!")

        session_id = st.session_state.session_id
        slices = st.session_state.slices

        if len(slices) == 0:
            st.error("⚠️ No slices found! Please go back and try again.")
            if st.button("⬅️ Start Over"):
                st.session_state.stage = 1
                st.rerun()

        else:
            st.info(f"📊 **{len(slices)} slices** found — review and edit below")

            slices_to_delete = []

            for i, slice_info in enumerate(slices):
                with st.container():

                    # Slice header
                    if slice_info['punctuation'] == 'INSERTED':
                        header = f"🎵 Clip {i+1} — Inserted Audio ({slice_info['duration']}s)"
                        border_color = "#764ba2"
                    elif slice_info['punctuation'] == 'SILENCE':
                        header = f"🔇 Silence {i+1} — {slice_info['duration']}s"
                        border_color = "#333"
                    else:
                        header = f"Slice {i+1} — {slice_info['start_time']}s → {slice_info['end_time']}s ({slice_info['duration']}s)"
                        border_color = "#667eea"

                    st.markdown(f"""
                    <div style='border-left: 3px solid {border_color};
                                padding: 10px 15px;
                                background: #1a1a2e;
                                border-radius: 0 8px 8px 0;
                                margin: 8px 0'>
                        <b style='color:white'>{header}</b><br>
                        <span style='color:#aaa; font-size:13px'>📝 {slice_info['text_segment']}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns([5, 1])

                    with col1:
                        # Audio player
                        audio_url = f"{API_URL}/slice/{session_id}/{slice_info['filename']}"
                        st.audio(audio_url, format="audio/mp3")

                    with col2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"delete_{i}", help="Delete this slice"):
                            api_delete(f"{API_URL}/slice/{session_id}/{slice_info['filename']}")
                            slices_to_delete.append(i)

                    # Pause input
                    if i < len(slices) - 1:
                        pause_val = st.number_input(
                            f"⏸️ Pause after Slice {i+1} (ms)",
                            min_value=0,
                            max_value=10000,
                            value=int(slice_info['pause_after_ms']),
                            step=500,
                            key=f"pause_{i}"
                        )
                        st.session_state.slices[i]['pause_after_ms'] = pause_val

                    # ➕ Insert panel
                    if i < len(slices) - 1:
                        with st.expander(f"➕ Insert something after Slice {i+1}"):

                            insert_type = st.radio(
                                "What to insert?",
                                options=["🔇 Silence", "🎵 Audio Clip"],
                                horizontal=True,
                                key=f"insert_type_{i}"
                            )

                            if insert_type == "🔇 Silence":
                                silence_duration = st.number_input(
                                    "Silence duration (ms)",
                                    min_value=500,
                                    max_value=30000,
                                    value=2000,
                                    step=500,
                                    key=f"silence_dur_{i}"
                                )
                                if st.button("➕ Add Silence", key=f"add_silence_{i}"):
                                    with st.spinner("Adding silence..."):
                                        response, error = api_post(
                                            f"{API_URL}/insert-silence",
                                            data={
                                                "session_id": session_id,
                                                "position": i + 1,
                                                "duration_ms": silence_duration,
                                                "slices_data": json.dumps(st.session_state.slices)
                                            }
                                        )
                                        if error:
                                            st.error(error)
                                        elif response.status_code == 200:
                                            st.session_state.slices = response.json()["slices"]
                                            st.success("✅ Silence added!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to add silence!")

                            elif insert_type == "🎵 Audio Clip":
                                clip_file = st.file_uploader(
                                    "Upload audio clip",
                                    type=["mp3", "wav"],
                                    key=f"clip_upload_{i}"
                                )
                                if clip_file and st.button("➕ Add Clip", key=f"add_clip_{i}"):
                                    with st.spinner("Adding clip..."):
                                        response, error = api_post(
                                            f"{API_URL}/insert-clip",
                                            files={"clip_file": (clip_file.name, clip_file, "audio/mpeg")},
                                            data={
                                                "session_id": session_id,
                                                "position": i + 1,
                                                "slices_data": json.dumps(st.session_state.slices)
                                            }
                                        )
                                        if error:
                                            st.error(error)
                                        elif response.status_code == 200:
                                            st.session_state.slices = response.json()["slices"]
                                            st.success("✅ Clip added!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to add clip!")

            # Remove deleted slices
            if slices_to_delete:
                st.session_state.slices = [
                    s for idx, s in enumerate(st.session_state.slices)
                    if idx not in slices_to_delete
                ]
                st.rerun()

            st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Start Over", use_container_width=True):
                    st.session_state.stage = 1
                    st.session_state.slices = []
                    st.session_state.session_id = None
                    st.rerun()

            with col2:
                if st.button("🎵 Stitch Final Audio →", use_container_width=True, type="primary"):
                    if len(st.session_state.slices) == 0:
                        st.error("No slices to stitch!")
                    else:
                        with st.spinner("🎵 Stitching your audio..."):
                            response, error = api_post(
                                f"{API_URL}/stitch",
                                data={
                                    "session_id": session_id,
                                    "slices_data": json.dumps(st.session_state.slices)
                                },
                                timeout=300
                            )
                            if error:
                                st.error(error)
                            elif response.status_code == 200:
                                st.session_state.final_audio = response.content
                                st.session_state.final_audio_path = f"outputs/{session_id}_final.mp3"
                                st.session_state.stage = 4
                                st.rerun()
                            else:
                                st.error("Stitching failed!")

    # ════════════════════════════════════════════════════
    # STAGE 4 — FINAL AUDIO
    # ════════════════════════════════════════════════════
    elif st.session_state.stage == 4:

        st.title("✅ Final Audio Ready!")
        st.markdown("<p style='color:#888'>Your audio has been stitched with custom pauses</p>", unsafe_allow_html=True)
        st.warning("⚠️ Download your audio before refreshing!")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
        <div style='background:#1a1a2e; border-radius:12px; padding:20px; text-align:center;
                    border: 1px solid #667eea'>
            <p style='color:#667eea; font-size:18px; margin:0'>🎵 Your Processed Audio</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.audio(st.session_state.final_audio, format="audio/mp3")

        st.download_button(
            label="⬇️ Download Final Audio",
            data=st.session_state.final_audio,
            file_name="final_audio.mp3",
            mime="audio/mpeg",
            use_container_width=True,
            type="primary"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Start Over", use_container_width=True):
                for key in ["slices", "session_id", "final_audio",
                           "final_audio_path", "bgm_audio"]:
                    st.session_state[key] = [] if key == "slices" else None
                st.session_state.stage = 1
                st.rerun()

        with col2:
            if st.button("🎵 Add BGM →", use_container_width=True, type="primary"):
                st.session_state.stage = 5
                st.rerun()

    # ════════════════════════════════════════════════════
    # STAGE 5 — BGM SETTINGS
    # ════════════════════════════════════════════════════
    elif st.session_state.stage == 5:

        st.title("🎵 Add Background Music")
        st.markdown("<p style='color:#888'>Upload a BGM track to play behind your audio</p>", unsafe_allow_html=True)
        st.warning("⚠️ Don't refresh — you'll lose your progress!")

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("Your Current Audio")
        st.audio(st.session_state.final_audio, format="audio/mp3")

        st.markdown("---")

        bgm_file = st.file_uploader(
            "🎼 Upload BGM File (MP3 or WAV)",
            type=["mp3", "wav"],
            key="bgm_upload"
        )

        if bgm_file:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("⚙️ BGM Settings")

            col1, col2 = st.columns(2)
            with col1:
                bgm_volume = st.slider(
                    "🎵 BGM Volume",
                    min_value=0, max_value=100,
                    value=30, step=5,
                    help="Volume of background music"
                )
            with col2:
                main_volume = st.slider(
                    "🎤 Voice Volume",
                    min_value=0, max_value=100,
                    value=100, step=5,
                    help="Volume of your main audio"
                )

            col3, col4 = st.columns(2)
            with col3:
                loop_bgm = st.checkbox(
                    "🔁 Loop BGM",
                    value=True,
                    help="Loop BGM to match full audio length"
                )
            with col4:
                fade_out = st.checkbox(
                    "📉 Fade Out at End",
                    value=False,
                    help="Smoothly fade BGM at the end"
                )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🎵 Apply BGM", use_container_width=True, type="primary"):
                with st.spinner("🎵 Adding background music..."):
                    response, error = api_post(
                        f"{API_URL}/add-bgm",
                        files={"bgm_file": (bgm_file.name, bgm_file, "audio/mpeg")},
                        data={
                            "session_id": st.session_state.session_id,
                            "final_audio_path": st.session_state.final_audio_path,
                            "bgm_volume": bgm_volume,
                            "main_volume": main_volume,
                            "loop": loop_bgm,
                            "fade_out": fade_out
                        },
                        timeout=300
                    )
                    if error:
                        st.error(error)
                    elif response.status_code == 200:
                        st.session_state.bgm_audio = response.content
                        st.session_state.stage = 6
                        st.rerun()
                    else:
                        st.error("Failed to add BGM!")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Back to Final Audio", use_container_width=True):
            st.session_state.stage = 4
            st.rerun()

    # ════════════════════════════════════════════════════
    # STAGE 6 — FINAL WITH BGM
    # ════════════════════════════════════════════════════
    elif st.session_state.stage == 6:

        st.title("🎉 Audio With BGM Ready!")
        st.markdown("<p style='color:#888'>Your audio with background music is ready</p>", unsafe_allow_html=True)
        st.warning("⚠️ Download before refreshing!")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("""
        <div style='background:#1a1a2e; border-radius:12px; padding:20px; text-align:center;
                    border: 1px solid #764ba2'>
            <p style='color:#764ba2; font-size:18px; margin:0'>🎵 Your Audio With Background Music</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.audio(st.session_state.bgm_audio, format="audio/mp3")

        st.download_button(
            label="⬇️ Download Audio With BGM",
            data=st.session_state.bgm_audio,
            file_name="final_with_bgm.mp3",
            mime="audio/mpeg",
            use_container_width=True,
            type="primary"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Change BGM", use_container_width=True):
                st.session_state.stage = 5
                st.session_state.bgm_audio = None
                st.rerun()
        with col2:
            if st.button("🔄 Process New Audio", use_container_width=True, type="primary"):
                for key in ["slices", "session_id", "final_audio",
                           "final_audio_path", "bgm_audio"]:
                    st.session_state[key] = [] if key == "slices" else None
                st.session_state.stage = 1
                st.rerun()