import streamlit as st
import joblib
import os
import string
import nltk
import pandas as pd
import streamlit_authenticator as stauth
from nltk.corpus import stopwords
from email_utils import connect_to_email, get_emails, clean_text_robust, check_phishing_risk
from db_utils import load_all_users, save_email_config, load_email_config, add_user_to_db, save_scan_result, get_user_analytics

# Set page configuration
st.set_page_config(page_title="SpamGuard Pro Intelligence", page_icon="🛡️", layout="wide")

# Load users from Database
credentials = load_all_users()

# Initialize authenticator
authenticator = stauth.Authenticate(
    credentials,
    "spam_detector_cookie",
    "spam_detector_secret_key",
    30
)

# Authentication logic
if not st.session_state.get("authentication_status"):
    login_tab, signup_tab = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with login_tab:
        try:
            authenticator.login(location='main')
        except Exception as e:
            st.error(f"Login error: {e}")
            
    with signup_tab:
        st.subheader("Create New Account")
        new_email = st.text_input("Email")
        new_username = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_password = st.text_input("Password", type="password")
        if st.button("Register"):
            if new_email and new_username and new_name and new_password:
                # Hash password
                hashed_pw = stauth.Hasher(passwords=[new_password]).generate()[0]
                if add_user_to_db(new_username, new_name, new_email, hashed_pw):
                    st.success("Registration successful! Please log in.")
                    st.balloons()
                else:
                    st.error("Username already exists.")
            else:
                st.warning("All fields are required.")

if st.session_state.get("authentication_status"):
    name = st.session_state["name"]
    username = st.session_state["username"]
    
    # Auto-load email connection
    if 'email_conn' not in st.session_state:
        email_cfg = load_email_config(username)
        if email_cfg:
            with st.spinner("Connecting to your secure inbox..."):
                conn = connect_to_email(
                    email_cfg['imap_server'], 
                    email_cfg['email_address'], 
                    email_cfg['app_password']
                )
                if conn:
                    st.session_state.email_conn = conn
                    st.toast(f"Welcome back, {name}! Inbox connected.", icon="🛡️")

    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/561/561127.png", width=100)
        st.title(f"Guard Status: Active")
        st.write(f"User: {name}")
        authenticator.logout('Logout', 'sidebar')
        st.write("---")
        if 'email_conn' in st.session_state and st.session_state.email_conn:
            st.success("📧 Mail: Online")
        else:
            st.warning("📧 Mail: Offline")

    # Load Model
    MODEL_PATH = 'model.pkl'
    VECTORIZER_PATH = 'vectorizer.pkl'
    @st.cache_resource
    def load_models():
        if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
            return joblib.load(MODEL_PATH), joblib.load(VECTORIZER_PATH)
        return None, None
    model, vectorizer = load_models()

    def predict_spam(text):
        cleaned = text.translate(str.maketrans(string.punctuation, " "*len(string.punctuation))).lower()
        try:
            stop_words = set(stopwords.words('english'))
        except:
            nltk.download('stopwords')
            stop_words = set(stopwords.words('english'))
        processed = " ".join([word for word in cleaned.split() if word not in stop_words])
        transformed = vectorizer.transform([processed])
        return model.predict(transformed)[0]

    st.title("🛡️ SpamGuard Pro Intelligence Platform")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📬 Inbox Scanner", 
        "🔍 Manual Check", 
        "📂 Bulk Scanner",
        "📊 Analytics", 
        "⚙️ Settings"
    ])

    with tab1:
        st.header("Inbox Intelligence")
        if 'email_conn' not in st.session_state:
            st.info("Connect your email in Settings to scan your inbox.")
        else:
            if st.button("🔄 Sync & Scan Latest Emails"):
                with st.spinner("Analyzing inbox traffic..."):
                    emails = get_emails(st.session_state.email_conn, limit=10)
                    st.session_state.recent_emails = emails
                    for em in emails:
                        p_body = clean_text_robust(em['body'])
                        pred = predict_spam(p_body)
                        risk = check_phishing_risk(em['body'])
                        save_scan_result(username, "Email", em['subject'], pred, risk)
            
            if 'recent_emails' in st.session_state:
                for em in st.session_state.recent_emails:
                    p_body = clean_text_robust(em['body'])
                    pred = predict_spam(p_body)
                    risk = check_phishing_risk(em['body'])
                    
                    status_class = "spam-badge" if pred == 1 else "ham-badge"
                    status_text = "SPAM" if pred == 1 else "LEGIT"
                    
                    with st.expander(f"[{status_text}] {em['subject']}"):
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.write(f"**From:** {em['sender']}")
                            st.text(em['body'][:1000] + "...")
                        with col_b:
                            st.markdown(f"**Intelligence Report**")
                            if pred == 1: st.error("🚨 Spam Detected")
                            else: st.success("✅ Legitimate")
                            
                            if risk > 50:
                                st.warning(f"⚠️ Phishing Risk: {risk}%")
                                st.progress(risk/100)
                            elif risk > 0:
                                st.info(f"🔗 URL Risk: {risk}%")
                            
                            if pred == 1: st.toast(f"Spam blocked: {em['subject']}", icon="🛡️")

    with tab2:
        st.header("Individual Intelligence Check")
        user_input = st.text_area("Paste message content:", height=200)
        if st.button("Analyze Content", type="primary"):
            if user_input:
                pred = predict_spam(user_input)
                risk = check_phishing_risk(user_input)
                save_scan_result(username, "Manual", user_input, pred, risk)
                
                if pred == 1:
                    st.error("### 🚨 HIGH SPAM ALERT")
                else:
                    st.success("### ✅ LEGITIMATE CONTENT")
                
                if risk > 0:
                    st.warning(f"**Phishing Risk Level:** {risk}%")
                    st.progress(risk/100)

    with tab4:
        st.header("Security Analytics Dashboard")
        stats = get_user_analytics(username)
        if stats and stats['total_scans'] > 0:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Scanned", stats['total_scans'])
            m2.metric("Spam Blocked", stats['spam_count'], delta=f"{stats['spam_count']/stats['total_scans']*100:.1f}%", delta_color="inverse")
            m3.metric("Phishing Alerts", stats['phishing_alerts'])
            
            # Simple Chart
            df = pd.DataFrame([
                {"Label": "Spam", "Count": stats['spam_count']},
                {"Label": "Legit", "Count": stats['ham_count']}
            ])
            st.write("### Threat Distribution")
            st.bar_chart(df.set_index("Label"))
            
            st.write("### Recent Activity Log")
            st.table(stats['history'][-10:])
        else:
            st.info("No scan history yet. Start scanning to see analytics!")

    with tab3:
        st.header("Bulk Analysis Portal")
        uploaded_file = st.file_uploader("Upload CSV or TXT file (column named 'message' or 'text')", type=['csv', 'txt'])
        if uploaded_file:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.DataFrame(uploaded_file.read().decode().splitlines(), columns=['message'])
            
            target_col = 'message' if 'message' in df.columns else ('text' if 'text' in df.columns else df.columns[0])
            st.write(f"Analyzing {len(df)} messages using column: `{target_col}`")
            
            if st.button("Run Bulk Intelligence"):
                with st.spinner("Processing large dataset..."):
                    df['Prediction'] = df[target_col].apply(lambda x: "SPAM" if predict_spam(str(x)) == 1 else "LEGIT")
                    df['URL_Risk'] = df[target_col].apply(lambda x: check_phishing_risk(str(x)))
                    
                    st.success("Analysis Complete!")
                    st.dataframe(df)
                    st.download_button("Download Report", df.to_csv(index=False), "spam_report.csv", "text/csv")

    with tab5:
        st.header("Intelligence Settings")
        email_cfg = load_email_config(username)
        saved_email = email_cfg['email_address'] if email_cfg else ""
        saved_server = email_cfg['imap_server'] if email_cfg else "imap.gmail.com"
        
        provider = st.selectbox("Mail Provider", ["Gmail", "Outlook", "Custom"], 
                               index=0 if "gmail" in saved_server else (1 if "outlook" in saved_server else 2))
        
        server = "imap.gmail.com" if provider == "Gmail" else ("imap-mail.outlook.com" if provider == "Outlook" else st.text_input("IMAP Server", saved_server))
        email_addr = st.text_input("Email Address", value=saved_email)
        app_pw = st.text_input("App Password", type="password")
        
        if st.button("Save Intelligence Settings"):
            with st.spinner("Verifying and saving..."):
                conn = connect_to_email(server, email_addr, app_pw)
                if conn:
                    st.session_state.email_conn = conn
                    save_email_config(username, server, email_addr, app_pw)
                    st.success("Settings saved to Neon DB!")
                else:
                    st.error("Verification failed. Check your App Password.")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; white-space: pre-wrap; background-color: #f0f2f6; 
        border-radius: 10px 10px 0px 0px; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #e0e2e6; font-weight: bold; }
    .spam-badge { color: #ff4b4b; font-weight: bold; }
    .ham-badge { color: #28a745; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)
st.caption("🛡️ SpamGuard Pro v3.0 Intelligence Platform • Advanced Security via Scikit-Learn & Neon DB")
