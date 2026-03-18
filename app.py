import streamlit as st
from db import init_db, add_user, get_user_by_email, save_upload, get_user_uploads
from utils import extract_text_from_pdf, sanitize_filename
from nlp import parse_resume_text_for_meta
from ml import load_internships, Matcher
import hashlib, json, pandas as pd
from fpdf import FPDF
from datetime import datetime

#Initialization 
@st.cache_resource
def setup_database():
    init_db()
    return True
setup_database()

@st.cache_resource
def get_matcher():
    df = load_internships('internships.csv')
    return Matcher(df)
matcher = get_matcher()

def hash_pw(pw: str):
    return hashlib.sha256(pw.encode()).hexdigest()

# Page Setup
st.set_page_config(page_title="Welcome to Internify", page_icon="🎓", layout="wide")

# ---------------- Global CSS ---------------- #
st.markdown("""
<style>
.load-fonts { font-family: 'Inter', 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@400;600;700;800&display=swap');

:root {
  --bg: #eef2ff;
  --bg-2: #e2e8f0;
  --text: #0f172a;
  --muted: #334155;
  --brand-700: #1d4ed8;
  --brand-800: #1e40af;
  --brand-600: #2563eb;
  --ring: rgba(37, 99, 235, 0.18);
  --card: #ffffff;
  --border: #d0d7e2;
  --shadow: rgba(0, 0, 0, 0.09);
}

.stApp {
  background: radial-gradient(85% 120% at 10% 10%, #f5f7ff 0%, var(--bg) 50%, var(--bg-2) 100%);
  font-family: 'Inter', 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  color: var(--text);
}

.main-title {
  font-size: 44px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--brand-700);
  text-align: center;
  margin-bottom: 10px;
}
.subtitle {
  text-align: center;
  color: var(--muted);
  margin-bottom: 28px;
  font-weight: 500;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 40%, #1e3a8a 100%);
  color: #f8fafc !important;
}
section[data-testid="stSidebar"] .stRadio > label, 
section[data-testid="stSidebar"] .stMarkdown {
  color: #f8fafc !important;
  font-weight: 500;
}
section[data-testid="stSidebar"] .sidebar-card {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 10px 18px rgba(0,0,0,0.18) inset;
}

/* Card container */
.card {
  background: var(--card);
  border-radius: 14px;
  padding: 20px;
  border: 1px solid var(--border);
  box-shadow: 0 6px 20px var(--shadow);
  transition: transform .15s ease, box-shadow .15s ease;
}
.card:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 26px rgba(0,0,0,.12);
}

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
  background-color: #ffffff !important;
  border-radius: 10px !important;
  border: 1.5px solid #cbd5e1 !important;
  color: #0f172a !important;
  font-weight: 500;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05) inset, 0 0 0 0 var(--ring);
}
.stTextInput:focus-within input,
.stSelectbox:focus-within div[role="combobox"],
.stTextArea:focus-within textarea {
  border-color: var(--brand-600) !important;
  box-shadow: 0 0 0 4px var(--ring) !important;
}

/* Buttons */
.stButton>button {
  background: linear-gradient(90deg, var(--brand-800), #3b82f6);
  color: white;
  border: none;
  padding: 12px 26px;
  font-weight: 600;
  border-radius: 8px;
  box-shadow: 0 8px 18px rgba(30,64,175,.25);
  transition: all 0.2s ease-in-out;
}
.stButton>button:hover {
  background: linear-gradient(90deg, #2563eb, #60a5fa);
  transform: translateY(-2px);
}

/* Intern cards */
.intern-card {
  background: var(--card);
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 18px rgba(0,0,0,0.06);
  transition: 0.15s ease-in-out;
  padding: 16px;
}
.intern-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 28px rgba(0,0,0,0.10);
}

/* Skill tags */
.pill {
  display:inline-block;
  background:#e0e7ff;
  color:#1e3a8a;
  border-radius:999px;
  font-size:12px;
  padding:5px 10px;
  margin:2px 4px;
  font-weight: 600;
}

/* Apply button */
.apply-btn {
  display:inline-block;
  background: linear-gradient(90deg, #16a34a, #22c55e);
  color:white !important;
  padding:8px 20px;
  border-radius:10px;
  text-decoration:none;
  font-weight:600;
  font-size:14px;
  transition: all 0.2s ease-in-out;
}
.apply-btn:hover {
  background: linear-gradient(90deg, #22c55e, #86efac);
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(22,163,74,.25);
}

/* Footer */
.footer {
  text-align:center;
  color:#475569;
  font-size:14px;
  margin-top:50px;
}

/* Contact buttons */
.contact-btn {
  display:inline-block;
  padding:10px 18px;
  background:linear-gradient(90deg,#0ea5e9,#22d3ee);
  color:white !important;
  border-radius:10px;
  text-decoration:none;
  font-weight:700;
  box-shadow: 0 8px 18px rgba(14,165,233,.25);
  transition: transform .15s ease, box-shadow .15s ease;
}
.contact-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 26px rgba(14,165,233,.32);
}
</style>
""", unsafe_allow_html=True)

# ---------------- Sidebar ---------------- #
st.sidebar.title("📂 Navigation")
menu = st.sidebar.radio("Navigate", ["🏠 Home", "🔑 Login", "📝 Signup", "ℹ️ About"])

# ---------------- Home ---------------- #
if menu == "🏠 Home":
    st.markdown('<h1 class="main-title">🎓 INTERNIFY</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Upload your resume → Extract skills → Get best-matched internships</p>', unsafe_allow_html=True)

    c1, c2 = st.columns([5,5])
    with c1:
        st.image("https://cdn-icons-png.flaticon.com/512/4228/4228702.png", width=360)
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("""
        <h3>🚀 How it works</h3>
        <ol style="line-height:1.9;">
          <li><b>Signup / Login</b> to create your profile</li>
          <li><b>Upload</b> your Resume (PDF)</li>
          <li>AI <b>NLP</b> extracts your skills</li>
          <li><b>ML engine</b> matches top internships</li>
          <li>Click <b>Apply Now</b> to go to official site</li>
        </ol>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.success("Built for students — clean, fast, and accurate 🔍")

# ---------------- Signup ---------------- #
elif menu == "📝 Signup":
    st.markdown('<h2>🧾 Create Your Account</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    name = st.text_input("👤 Full Name")
    email = st.text_input("📧 Email Address")
    password = st.text_input("🔒 Password", type="password")
    if st.button("Create Account"):
        if get_user_by_email(email):
            st.error("This email is already registered. Please login.")
        else:
            add_user(name, email, hash_pw(password))
            st.success("✅ Account created! Please login to continue.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Login ---------------- #
elif menu == "🔑 Login":
    st.markdown('<h1 class="main-title">👤 Login to Continue</h1>', unsafe_allow_html=True)
    email = st.text_input("📧 Email", placeholder="Enter your registered email")
    password = st.text_input("🔒 Password", placeholder="Enter your password", type="password")
    if st.button("Login"):
        row = get_user_by_email(email)
        if not row:
            st.error("No account found with this email.")
        else:
            user_id, name, email_db, pw_hash = row
            if hash_pw(password) == pw_hash:
                st.session_state['user'] = {'id': user_id, 'name': name, 'email': email_db}
                st.success(f"Welcome back, {name}! 🎉")
            else:
                st.error("Incorrect password. Please try again.")

# ---------------- Dashboard ---------------- #
# ---------------- Dashboard ---------------- #
if "user" in st.session_state:
    user = st.session_state["user"]
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"👋 Logged in as: **{user['name']}**")
    st.sidebar.subheader("Dashboard")

    # ✅ Unified dropdown for dashboard options
    action = st.sidebar.selectbox("", ["📤 Upload Resume", "📁 View Past Results", "⚙️ Edit Profile", "🚪 Logout"])

    # ---------------- Logout ---------------- #
    if action == "🚪 Logout":
        del st.session_state["user"]
        st.experimental_rerun()

    # ---------------- Upload Resume ---------------- #
    elif action == "📤 Upload Resume":
        # (Keep your existing upload resume code here, unchanged)
        pass

    # ---------------- View Past Results ---------------- #
    elif action == "📁 View Past Results":
        st.markdown('<h2 style="margin-bottom:14px;">🕓 Your Previous Uploads</h2>', unsafe_allow_html=True)
        uploads = get_user_uploads(user["id"])
        if not uploads:
            st.info("No uploads yet. Upload your first resume to begin.")
        else:
            for up in uploads:
                st.markdown(f'<div class="card" style="margin-bottom:12px;"><b>{up["resume_name"]}</b> — Uploaded on {up["timestamp"]}</div>', unsafe_allow_html=True)
                for t in up["top_internships"]:
                    st.markdown(f"""
                    <div class="intern-card" style="margin-bottom:10px;">
                        <div style="display:flex;justify-content:space-between;align-items:start;">
                            <div>
                                <div style="font-weight:800;font-size:15px;margin-bottom:6px;">{t["title"]}</div>
                                <div style="color:#64748b;font-size:13px;margin-bottom:8px;">{t["company"]}</div>
                            </div>
                            <div style="color:#2357d8;font-weight:800;">{t.get("match_percent","-")}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ---------------- Edit Profile ---------------- #
    elif action == "⚙️ Edit Profile":
        st.markdown('<h2 style="margin-bottom:14px;">⚙️ Edit Profile</h2>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Full Name", value=user["name"])
            st.text_input("Email", value=user["email"])
        with c2:
            st.text_input("Phone", placeholder="+91-")
            st.text_input("Location", placeholder="City, Country")
        st.caption("Profile editing is a placeholder in this version.")
        st.markdown("</div>", unsafe_allow_html=True)

    if action == "🚪 Logout":
        del st.session_state['user']
        st.experimental_rerun()

    elif action == "📤 Upload Resume":
        st.markdown('<h2>📄 Upload Resume</h2>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload your Resume (PDF only)", type=['pdf'])
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            loc = st.selectbox("📍 Location", ["", "Remote", "Onsite", "Hyderabad", "Bangalore", "Mumbai", "Delhi", "Noida", "Gurugram"])
        with colf2:
            domain = st.selectbox("💼 Domain", ["", "Data Science", "Web Dev", "Machine Learning", "Finance", "Mobile"])
        with colf3:
            sort_by = st.selectbox("Sort By", ["match_percent", "company"])
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_file:
            with st.spinner("🔍 Analyzing your resume..."):
                bytes_data = uploaded_file.read()
                text = extract_text_from_pdf(bytes_data)
                meta = parse_resume_text_for_meta(text)
                skills = meta.get('skills', [])

                # Resume Summary
                st.markdown('<div class="card" style="margin-top:14px;">', unsafe_allow_html=True)
                st.subheader("📘 Resume Summary")

                c1, c2 = st.columns([1, 2])

                with c1:
                    # ✅ Safe name extraction with fallback
                    detected_name = meta.get('name')
                    if isinstance(detected_name, (list, dict)):
                        detected_name = None
                    if not detected_name or str(detected_name).strip().lower() in ["none", "", "null"]:
                        detected_name = user.get('name', 'N/A')
                    st.write("**Name:**", detected_name)

                    # ✅ Fix: Handle missing or invalid emails
                    emails = meta.get('emails', [])
                    if not emails or not isinstance(emails, list) or all(e.strip() == "" for e in emails):
                        emails = [user.get('email', 'N/A')]
                    st.write("**Email(s):**", ", ".join(emails))

                with c2:
                    st.write("**Extracted Skills:**")
                    skills = meta.get('skills', [])
                    if skills:
                        st.markdown("".join([f'<span class="pill">{s}</span>' for s in skills]), unsafe_allow_html=True)
                    else:
                        st.info("No skills detected.")

                st.markdown('</div>', unsafe_allow_html=True)


                # Match internships
                filters = {}
                if loc: filters['location'] = loc
                if domain: filters['domain'] = domain
                results = matcher.match(text, top_k=5, filters=filters)

                st.markdown('<h3 style="margin-top:20px;margin-bottom:10px;">🎯 Top Internship Recommendations</h3>', unsafe_allow_html=True)
                grid = st.columns(5 if len(results) >= 5 else len(results) or 1)

                for idx, r in enumerate(results[:5]):
                    with grid[idx % len(grid)]:
                        apply_link = r.get('apply_link', '#')
                        st.markdown(f"""
                        <div class="intern-card">
                            <div style="display:flex;justify-content:space-between;align-items:start;">
                                <div>
                                    <div style="font-weight:800;font-size:16px;margin-bottom:6px;">{r['title']}</div>
                                    <div style="color:#64748b;font-size:13px;margin-bottom:8px;">{r['company']}</div>
                                </div>
                                <div style="color:#2357d8;font-weight:800;">{r['match_percent']}%</div>
                            </div>
                            <div style="font-size:13px;margin:4px 0 10px 0;"><b>📍 Location:</b> {r.get('location', 'N/A')}</div>
                            <div style="font-size:13px;"><b>Skills Required:</b></div>
                            <div style="margin-top:6px;">{''.join([f'<span class="pill">{s.strip()}</span>' for s in r['skills'].split(',') if s.strip()])}</div>
                            <div style="text-align:center;margin-top:12px;">
                                <a href="{apply_link}" target="_blank" class="apply-btn">🚀 Apply Now</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # Save results
                skill_matches = {}
                for r in results:
                    req_skills = [s.strip().lower() for s in r['skills'].split(',') if s.strip()]
                    matched = [s for s in req_skills if s in [x.lower() for x in skills]]
                    missing = [s for s in req_skills if s not in [x.lower() for x in skills]]
                    skill_matches[f"{r['company']}|{r['title']}"] = {
                        'matched': matched,
                        'missing': missing,
                        'match_percent': r['match_percent']
                    }

                save_upload(user_id=user['id'], resume_name=sanitize_filename(uploaded_file.name),
                            top_internships=results, skill_matches=skill_matches)

                # Graph Section
                st.markdown('<div class="card" style="margin-top:14px;">', unsafe_allow_html=True)
                if st.button("📊 View Skill Match Graph"):
                    df_graph = pd.DataFrame(
                        [{'internship': k, 'match_percent': v['match_percent']} for k, v in skill_matches.items()]
                    )
                    st.bar_chart(df_graph.set_index('internship'))
                st.markdown('</div>', unsafe_allow_html=True)

# ---------------- About ---------------- #
elif menu == "ℹ️ About":
    st.markdown('<h1 class="main-title">About Internship Finder AI</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card" style="max-width:900px;margin:auto;">
      <p><b>Internship Finder AI</b> uses NLP and ML to analyze resumes and match students with relevant internships.</p>
      <ul style="line-height:1.9;color:#374151">
        <li><b>Tech Stack:</b> Python, Streamlit, SQLite, NLP, ML, and FPDF</li>
        <li><b>Audience:</b> Engineering & Computer Science Students</li>
        <li><b>Goal:</b> Bridge the gap between academia and industry experience</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<h3 style="text-align:center;margin:8px 0 16px 0;">📞 Contact Us</h3>', unsafe_allow_html=True)
    cA, cB, cC = st.columns(3)
    with cA:
        st.markdown('<a href="tel:+918534095607" class="contact-btn">📞 Call Us</a>', unsafe_allow_html=True)
    with cB:
        st.markdown('<a href="https://wa.me/918534095607" class="contact-btn">💬 WhatsApp</a>', unsafe_allow_html=True)
    with cC:
        st.markdown('<a href="mailto:support@internfinder.ai" class="contact-btn">📧 Email</a>', unsafe_allow_html=True)

# ---------------- Global Footer ---------------- #
st.markdown('<div class="footer">© 2025 Internify • Made with ❤️ for students</div>', unsafe_allow_html=True)
