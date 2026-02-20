import streamlit as st
import pandas as pd
import datetime
import random
import json
import gspread
from google.oauth2.service_account import Credentials

# Set the page configuration
st.set_page_config(page_title="Student Tracker Pro", page_icon="🎓", layout="wide")

# ==========================================
# --- GOOGLE SHEETS DATABASE CONNECTION ---
# ==========================================
@st.cache_resource
def init_gsheets():
    try:
        raw_json = st.secrets["google_json"]
        creds_dict = json.loads(raw_json, strict=False)
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        return None

client = init_gsheets()
DB_NAME = "StudentTracker_DB"

# FUNGSI MAGIK: Load & Auto-Create Tab di Google Sheets
def load_data(ws_name, cols, bool_cols=[], float_cols=[]):
    df = pd.DataFrame(columns=cols)
    if client:
        try:
            sheet = client.open(DB_NAME)
            try:
                ws = sheet.worksheet(ws_name)
            except gspread.exceptions.WorksheetNotFound:
                # Kalau tab tak wujud, buat baru automatik!
                ws = sheet.add_worksheet(title=ws_name, rows="100", cols=str(len(cols)))
                ws.update(range_name="A1", values=[cols])
                return df
            
            records = ws.get_all_records()
            if records:
                df = pd.DataFrame(records)
        except Exception as e:
            pass
            
    # Formatkan jenis data supaya tak berlaku ralat matematik
    for c in bool_cols:
        if c in df.columns: df[c] = df[c].astype(str).str.lower() == 'true'
    for c in float_cols:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
            
    for c in cols:
        if c not in df.columns: df[c] = ""
    return df[cols]

# Fungsi Simpan Data ke Google Sheets
def save_data(ws_name, df):
    if client and not df.empty:
        try:
            df_clean = df.copy().fillna("").astype(str)
            sheet = client.open(DB_NAME)
            ws = sheet.worksheet(ws_name)
            ws.clear()
            ws.update(range_name="A1", values=[df_clean.columns.values.tolist()] + df_clean.values.tolist())
        except Exception as e:
            pass

# --- INITIALIZE SEMUA DATABASE ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = load_data("To_Do_List", ["Status", "Task", "Subject", "Deadline", "Priority", "Notes"], bool_cols=["Status"])
if 'scholarships' not in st.session_state:
    st.session_state.scholarships = load_data("Scholarships", ["Scholarship Name", "Bond", "Due Date", "App Status", "Result"])
if 'cgpa_data' not in st.session_state:
    st.session_state.cgpa_data = load_data("CGPA", ["Semester", "Code", "Subject", "Credit", "Grade", "Pointer"], float_cols=["Pointer"], bool_cols=[])
    # Betulkan format jam kredit selepas load dari database
    if not st.session_state.cgpa_data.empty:
        st.session_state.cgpa_data['Credit'] = pd.to_numeric(st.session_state.cgpa_data['Credit'], errors='coerce').fillna(0).astype(int)

# Load Targets khas
if 'sem_targets' not in st.session_state:
    df_targets = load_data("Targets", ["Semester", "Subjects", "Credits"])
    targets_dict = {}
    if not df_targets.empty:
        for idx, row in df_targets.iterrows():
            targets_dict[row["Semester"]] = {"subjects": int(row["Subjects"]), "credits": int(row["Credits"])}
    st.session_state.sem_targets = targets_dict

if 'assignments' not in st.session_state:
    st.session_state.assignments = load_data("Assignments", ["Project Name", "Subject", "Team Members", "Status", "Due Date"])
if 'finances' not in st.session_state:
    st.session_state.finances = load_data("Finances", ["Date", "Type", "Category", "Amount", "Description"], float_cols=["Amount"])
if 'schedule' not in st.session_state:
    st.session_state.schedule = load_data("Schedule", ["Day", "Time", "Subject", "Location"])

if 'exam_date' not in st.session_state:
    st.session_state.exam_date = datetime.date.today() + datetime.timedelta(days=60)
if 'quick_notes' not in st.session_state:
    st.session_state.quick_notes = "Jot down your sudden ideas or reminders here..."

grade_map = {"A+": 4.00, "A": 4.00, "A-": 3.67, "B+": 3.33, "B": 3.00, "B-": 2.67, "C+": 2.33, "C": 2.00, "C-": 1.67, "D+": 1.33, "D": 1.00, "D-": 0.67, "E": 0.00}

# --- SIDEBAR & LOGO ---
try: st.sidebar.image("logo_utm.png", use_container_width=True)
except: pass 
st.sidebar.title("Navigation Menu")
page_selection = st.sidebar.radio("Go to:", ["🏠 Main Dashboard", "📝 To-Do List", "👥 Project Manager", "💰 Financial Tracker", "📅 Class Schedule", "💡 Quick Notes", "🎓 Scholarship Tracker", "📊 CGPA Tracker"])

# --- 1. MAIN DASHBOARD ---
if page_selection == "🏠 Main Dashboard":
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.title("Welcome back, Shamsir! 🎓")
        st.write("Your command center for UTM Kuala Lumpur studies.")
    with col_header2:
        try: st.image("cat_study.png", width=150)
        except: pass

    quotes = [
        "Kejayaan bukan pecutan, ia macam larian half marathon. Pace yourself, keep breathing, and stay consistent. 🏃‍♂️",
        "Debugging AI models boleh buat pening, tapi ingat wajah gembira Mak dan Ayah bila tengok result kau nanti. 💻",
        "Setiap baris kod yang disiapkan dan setiap botol sambal ikan bilis yang terjual adalah langkah ke arah kebebasan kewangan. 🌶️",
        "Bila rasa burnout, ingat balik kenapa kau mula. Banggakan Atok, Along, Hajar, Hawa, Majid, dan Amri! 👨‍👩‍👧‍👦",
        "The best way to predict the future is to create it. Teruskan pulun degree kat UTM ni! 🎓"
    ]
    today_quote = quotes[datetime.date.today().timetuple().tm_yday % len(quotes)]
    st.info(f"💡 **Quote of the Day:**\n\n*{today_quote}*")
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    pending_tasks = len(st.session_state.tasks[st.session_state.tasks["Status"] == False]) if not st.session_state.tasks.empty else 0
    col1.metric("Pending Tasks", f"{pending_tasks} Tasks")
    total_in = st.session_state.finances[st.session_state.finances["Type"] == "Income"]["Amount"].sum() if not st.session_state.finances.empty else 0
    total_out = st.session_state.finances[st.session_state.finances["Type"] == "Expense"]["Amount"].sum() if not st.session_state.finances.empty else 0
    col2.metric("Financial Balance", f"RM {(total_in - total_out):.2f}")
    if not st.session_state.cgpa_data.empty:
        df_all = st.session_state.cgpa_data
        cgpa_val = (df_all['Credit'] * df_all['Pointer']).sum() / df_all['Credit'].sum() if df_all['Credit'].sum() > 0 else 0.0
    else: cgpa_val = 0.0
    col3.metric("Current CGPA", f"{cgpa_val:.2f}")
    days_to_exam = (st.session_state.exam_date - datetime.date.today()).days
    col4.metric("Exam Countdown", f"{days_to_exam} Days")
    st.markdown("---")

    col_g1, col_g2, col_g3 = st.columns([1, 1, 1.5])
    with col_g1:
        st.write("📊 **Task Priorities**")
        if not st.session_state.tasks.empty:
            pending_df = st.session_state.tasks[st.session_state.tasks["Status"] == False]
            if not pending_df.empty: st.bar_chart(pending_df["Priority"].value_counts(), color="#88A2FF") 
            else: st.write("All clear! 🎉")
        else: st.write("No tasks yet.")
    with col_g2:
        st.write("📈 **Cashflow (In vs Out)**")
        if not st.session_state.finances.empty: st.bar_chart(st.session_state.finances.groupby("Type")["Amount"].sum(), color="#253A82")
        else: st.write("No data yet.")
    
    with col_g3:
        st.subheader("🔥 Today's Focus")
        st.write("Urgent tasks (due within 3 days):")
        if not st.session_state.tasks.empty:
            active_tasks = st.session_state.tasks[st.session_state.tasks["Status"] == False].copy()
            
            # KOD YANG TELAH DIBETULKAN UNTUK ERROR SEBELUM NI!
            # pd.to_datetime menukar teks ke format tarikh sebenar secara paksa
            active_tasks['Deadline_Date'] = pd.to_datetime(active_tasks['Deadline'], errors='coerce').dt.date
            today_date = datetime.date.today()
            active_tasks['Days Left'] = active_tasks['Deadline_Date'].apply(lambda x: (x - today_date).days if pd.notnull(x) else 99)
            
            urgent_tasks = active_tasks[active_tasks['Days Left'] <= 3]
            
            if not urgent_tasks.empty:
                for index, row in urgent_tasks.iterrows():
                    days_text = "Today!" if row['Days Left'] == 0 else f"{row['Days Left']} days left"
                    if row['Days Left'] < 0: days_text = "OVERDUE 🚨"
                    st.warning(f"**{row['Task']}** ({row['Subject']}) - {days_text}")
            else: st.success("No urgent tasks right now. Time for a break! ☕")
        else: st.info("Add tasks in the To-Do List.")
    st.markdown("---")
    st.subheader("💡 Scratchpad")
    new_note = st.text_area("Dump your thoughts here:", value=st.session_state.quick_notes, height=150)
    if new_note != st.session_state.quick_notes:
        st.session_state.quick_notes = new_note
        st.toast("Note auto-saved!", icon="🐱")

# --- 2. TO-DO LIST ---
elif page_selection == "📝 To-Do List":
    st.title("📝 Daily Tasks")
    if client: st.caption("🟢 Connected to Google Sheets Database")
    
    with st.expander("➕ Add New Task", expanded=False):
        with st.form("new_task_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                task_name = st.text_input("Task Name")
                subject_name = st.text_input("Course / Subject")
            with col2:
                deadline = st.date_input("Deadline")
                priority = st.selectbox("Priority Level", ["High", "Medium", "Low"])
            notes = st.text_area("Additional Notes")
            if st.form_submit_button("Add Task") and task_name:
                new_task = pd.DataFrame([{"Status": False, "Task": task_name, "Subject": subject_name, "Deadline": deadline, "Priority": priority, "Notes": notes}])
                st.session_state.tasks = pd.concat([st.session_state.tasks, new_task], ignore_index=True)
                save_data("To_Do_List", st.session_state.tasks) 
                st.success("Task added and saved to Database successfully!")

    if not st.session_state.tasks.empty:
        display_df = st.session_state.tasks.copy()
        today = datetime.date.today()
        def get_urgency(date_val):
            try:
                days_left = (pd.to_datetime(date_val).date() - today).days
                if days_left < 0: return "🚨 Overdue"
                elif days_left <= 3: return "🔴 Urgent"
                elif days_left <= 7: return "🟡 Soon"
                else: return "🟢 Chill"
            except: return "🟢 Chill"
                
        display_df.insert(1, "Urgency", display_df["Deadline"].apply(get_urgency))
        edited_df = st.data_editor(display_df, column_config={"Status": st.column_config.CheckboxColumn("Done?", default=False)}, disabled=["Urgency", "Task", "Subject", "Deadline", "Priority", "Notes"], hide_index=True, use_container_width=True)
        clean_edited_df = edited_df.drop(columns=["Urgency"])
        
        if not clean_edited_df.equals(st.session_state.tasks):
            st.session_state.tasks = clean_edited_df
            save_data("To_Do_List", st.session_state.tasks)

        if st.button("🧹 Clear Completed Tasks"):
            st.session_state.tasks = st.session_state.tasks[st.session_state.tasks["Status"] == False]
            save_data("To_Do_List", st.session_state.tasks) 
            st.rerun()

# --- 3. PROJECT MANAGER ---
elif page_selection == "👥 Project Manager":
    st.title("👥 Assignments & Group Projects")
    with st.expander("➕ Create New Project", expanded=False):
        with st.form("new_proj_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                proj_name = st.text_input("Project Name")
                subj_name = st.text_input("Course")
            with col2:
                members = st.text_input("Team Members (Comma separated)")
                due_date = st.date_input("Submission Date")
            if st.form_submit_button("Add Project") and proj_name:
                new_proj = pd.DataFrame([{"Project Name": proj_name, "Subject": subj_name, "Team Members": members, "Status": "Not Started", "Due Date": due_date}])
                st.session_state.assignments = pd.concat([st.session_state.assignments, new_proj], ignore_index=True)
                save_data("Assignments", st.session_state.assignments)
                st.success("Project added successfully!")
    if not st.session_state.assignments.empty:
        old_ass = st.session_state.assignments.copy()
        edited_proj = st.data_editor(st.session_state.assignments, column_config={"Status": st.column_config.SelectboxColumn("Progress", options=["Not Started", "In Progress", "Completed"], required=True)}, hide_index=True, use_container_width=True)
        if not old_ass.equals(edited_proj):
            st.session_state.assignments = edited_proj
            save_data("Assignments", st.session_state.assignments)

# --- 4. FINANCIAL TRACKER ---
elif page_selection == "💰 Financial Tracker":
    st.title("💰 Finance Tracker")
    tab1, tab2 = st.tabs(["📊 Overview", "➕ Add Transaction"])
    with tab2:
        with st.form("finance_form", clear_on_submit=True):
            f_type = st.radio("Transaction Type", ["Income", "Expense"], horizontal=True)
            f_cat = st.selectbox("Category", ["Food", "Business", "Transport", "Study Materials", "Personal", "Others"])
            f_amt = st.number_input("Amount (RM)", min_value=0.0, step=1.0)
            f_desc = st.text_input("Description")
            f_date = st.date_input("Date")
            if st.form_submit_button("Record Transaction") and f_amt > 0:
                new_fin = pd.DataFrame([{"Date": f_date, "Type": f_type, "Category": f_cat, "Amount": f_amt, "Description": f_desc}])
                st.session_state.finances = pd.concat([st.session_state.finances, new_fin], ignore_index=True)
                save_data("Finances", st.session_state.finances)
                st.success("Transaction recorded!")
    with tab1:
        if not st.session_state.finances.empty:
            df_fin = st.session_state.finances
            t_in = df_fin[df_fin["Type"] == "Income"]["Amount"].sum()
            t_out = df_fin[df_fin["Type"] == "Expense"]["Amount"].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Income", f"RM {t_in:.2f}")
            c2.metric("Total Expenses", f"RM {t_out:.2f}")
            c3.metric("Net Balance", f"RM {(t_in - t_out):.2f}")
            df_exp = df_fin[df_fin["Type"] == "Expense"]
            if not df_exp.empty:
                st.write("**Expense Breakdown**")
                st.bar_chart(df_exp.groupby("Category")["Amount"].sum(), color="#88A2FF")
            st.write("**Transaction History**")
            st.dataframe(df_fin, hide_index=True, use_container_width=True)

# --- 5. CLASS SCHEDULE ---
elif page_selection == "📅 Class Schedule":
    st.title("📅 Weekly Schedule & Countdown")
    col1, col2 = st.columns([2, 1])
    with col1:
        with st.expander("➕ Add Class Session", expanded=False):
            with st.form("class_form", clear_on_submit=True):
                c_day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
                c_time = st.text_input("Time (e.g., 10:00 AM - 12:00 PM)")
                c_sub = st.text_input("Course Name")
                c_loc = st.text_input("Location / Hall")
                if st.form_submit_button("Add Class"):
                    new_c = pd.DataFrame([{"Day": c_day, "Time": c_time, "Subject": c_sub, "Location": c_loc}])
                    st.session_state.schedule = pd.concat([st.session_state.schedule, new_c], ignore_index=True)
                    save_data("Schedule", st.session_state.schedule)
                    st.rerun()
        if not st.session_state.schedule.empty:
            st.dataframe(st.session_state.schedule, hide_index=True, use_container_width=True)
            if st.button("Kosongkan Jadual"):
                st.session_state.schedule = pd.DataFrame(columns=["Day", "Time", "Subject", "Location"])
                save_data("Schedule", st.session_state.schedule)
                st.rerun()
    with col2:
        st.write("### ⏳ Exam Countdown")
        new_exam = st.date_input("Set Final Exam Date", value=st.session_state.exam_date)
        if new_exam != st.session_state.exam_date: st.session_state.exam_date = new_exam
        days_left = (st.session_state.exam_date - datetime.date.today()).days
        if days_left > 0: st.info(f"**{days_left} days** remaining until finals. Keep pushing!")
        elif days_left == 0: st.warning("🚨 Finals begin TODAY! Best of luck!")

# --- 6. QUICK NOTES ---
elif page_selection == "💡 Quick Notes":
    st.title("💡 Unstructured Notes")
    st.write("A clean space for your brainstorming and sudden ideas.")
    note_content = st.text_area("Start typing...", value=st.session_state.quick_notes, height=400)
    if st.button("Save Notes"):
        st.session_state.quick_notes = note_content
        st.toast("Notes saved successfully!", icon="🐱")

# --- 7. SCHOLARSHIP TRACKER ---
elif page_selection == "🎓 Scholarship Tracker":
    st.title("🎓 Scholarship Applications")
    with st.expander("➕ Add New Application", expanded=False):
        with st.form("new_scholarship_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                sch_name = st.text_input("Scholarship Name")
                bond_status = st.selectbox("Bond Requirement?", ["Yes", "No", "Unsure"])
            with col2:
                due_date = st.date_input("Closing Date")
                app_status = st.selectbox("Application Status", ["Not Started", "In Progress", "Application Submitted"])
            sch_result = st.selectbox("Result Status", ["Pending Result", "Interview Stage", "Successful", "Unsuccessful"])
            if st.form_submit_button("Add Record") and sch_name:
                new_sch = pd.DataFrame([{"Scholarship Name": sch_name, "Bond": bond_status, "Due Date": due_date, "App Status": app_status, "Result": sch_result}])
                st.session_state.scholarships = pd.concat([st.session_state.scholarships, new_sch], ignore_index=True)
                save_data("Scholarships", st.session_state.scholarships)
                st.success("Record added!")
    if not st.session_state.scholarships.empty:
        old_df = st.session_state.scholarships.copy()
        edited_sch_df = st.data_editor(st.session_state.scholarships, column_config={"App Status": st.column_config.SelectboxColumn("App Status", options=["Not Started", "In Progress", "Application Submitted"], required=True), "Result": st.column_config.SelectboxColumn("Result", options=["Pending Result", "Interview Stage", "Successful", "Unsuccessful"], required=True)}, disabled=["Scholarship Name", "Bond", "Due Date"], hide_index=True, use_container_width=True)
        if not old_df.equals(edited_sch_df):
            for i in range(len(edited_sch_df)):
                try:
                    if old_df.iloc[i]["Result"] != edited_sch_df.iloc[i]["Result"]:
                        new_res = edited_sch_df.iloc[i]["Result"]
                        name = edited_sch_df.iloc[i]["Scholarship Name"]
                        if new_res == "Successful":
                            st.balloons()
                            try: st.image("cat_party.png", width=200)
                            except: pass
                            msgs = [f"🎉 ALHAMDULILLAH! Your hard work paid off for {name}!", f"🔥 Awesome! {name} secured. Time to celebrate!", f"🌟 Atok must be so proud of you getting {name}. Keep moving forward!"]
                            st.success(random.choice(msgs))
                        elif new_res == "Unsuccessful":
                            try: st.image("cat_support.png", width=200)
                            except: pass
                            st.info(f"💪 Don't be discouraged. Missing out on {name} just means something better is coming.")
                except IndexError: pass
            st.session_state.scholarships = edited_sch_df
            save_data("Scholarships", st.session_state.scholarships)

# --- 8. CGPA TRACKER ---
elif page_selection == "📊 CGPA Tracker":
    st.title("📊 Academic Performance")
    current_sem = st.selectbox("Select Semester:", ["Semester 1", "Semester 2", "Semester 3", "Semester 4", "Semester 5", "Semester 6", "Semester 7", "Semester 8"])
    st.markdown("---")
    
    if current_sem not in st.session_state.sem_targets:
        st.warning(f"Initialization required for {current_sem}.")
        with st.form(f"target_form_{current_sem}"):
            c_t1, c_t2 = st.columns(2)
            t_sub = c_t1.number_input("Total Subjects this semester?", min_value=1, step=1)
            t_cred = c_t2.number_input("Total Credit Hours this semester?", min_value=1, step=1)
            if st.form_submit_button("Confirm Initialization"):
                st.session_state.sem_targets[current_sem] = {"subjects": t_sub, "credits": t_cred}
                
                # Convert dict to df & save
                df_targets = pd.DataFrame.from_dict(st.session_state.sem_targets, orient='index').reset_index().rename(columns={'index':'Semester'})
                save_data("Targets", df_targets)
                st.rerun()
    else:
        t_sub = st.session_state.sem_targets[current_sem]["subjects"]
        df_sem = st.session_state.cgpa_data[st.session_state.cgpa_data['Semester'] == current_sem]
        curr_count = len(df_sem)
        tab_res, tab_hist = st.tabs(["📝 Record Results", "📋 Semester Overview"])
        with tab_res:
            if curr_count < t_sub:
                st.write(f"**Input Data ({curr_count}/{t_sub} Subjects Recorded)**")
                with st.form("cgpa_form", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    c_code = c1.text_input("Course Code (e.g., SCAI1013)")
                    c_name = c1.text_input("Course Name")
                    c_cred = c2.number_input("Credit Hours", min_value=1, max_value=6, step=1)
                    c_grd = c2.selectbox("Grade Achieved", list(grade_map.keys()))
                    if st.form_submit_button("Add Subject Record"):
                        new_sub = pd.DataFrame([{"Semester": current_sem, "Code": c_code, "Subject": c_name, "Credit": c_cred, "Grade": c_grd, "Pointer": grade_map[c_grd]}])
                        st.session_state.cgpa_data = pd.concat([st.session_state.cgpa_data, new_sub], ignore_index=True)
                        save_data("CGPA", st.session_state.cgpa_data)
                        st.rerun()
            else:
                gpa_val = (df_sem['Pointer'] * df_sem['Credit']).sum() / df_sem['Credit'].sum() if df_sem['Credit'].sum() > 0 else 0.0
                st.success(f"✅ All {t_sub} subjects recorded for {current_sem}!")
                st.markdown(f"## 🎯 GPA: **{gpa_val:.2f}**")
                if gpa_val >= 3.67:
                    if f"dekan_{current_sem}" not in st.session_state:
                        st.balloons()
                        st.session_state[f"dekan_{current_sem}"] = True
                    try: st.image("cat_party.png", width=200)
                    except: pass
                    st.success("MashaAllah Tabarakallah! Dean's List secured! Mak and Ayah must be so proud of you, Shamsir!")
                else:
                    try: st.image("cat_support.png", width=200)
                    except: pass
                    st.info(f"Alhamdulillah, finished with a {gpa_val:.2f}. Rest up, and let's push harder for the Dean's List next semester!")
                
                if st.button("Reset Semester Data", type="primary"):
                    st.session_state.cgpa_data = st.session_state.cgpa_data[st.session_state.cgpa_data['Semester'] != current_sem]
                    save_data("CGPA", st.session_state.cgpa_data)
                    del st.session_state.sem_targets[current_sem]
                    
                    df_targets = pd.DataFrame.from_dict(st.session_state.sem_targets, orient='index').reset_index().rename(columns={'index':'Semester'})
                    save_data("Targets", df_targets)
                    st.rerun()
        with tab_hist:
            st.dataframe(df_sem, hide_index=True, use_container_width=True)

    if not st.session_state.cgpa_data.empty:
        st.markdown("---")
        df_all = st.session_state.cgpa_data
        cgpa_tot = (df_all['Credit'] * df_all['Pointer']).sum() / df_all['Credit'].sum() if df_all['Credit'].sum() > 0 else 0.0
        st.write("### 🏆 Cumulative Performance")
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("Cumulative CGPA", f"{cgpa_tot:.2f}")
        c_m2.metric("Semesters Recorded", f"{len(st.session_state.sem_targets)}")
        st.write("📈 **GPA Trend**")
        trend = df_all.groupby('Semester').apply(lambda x: (x['Pointer'] * x['Credit']).sum() / x['Credit'].sum()).reset_index(name='GPA')
        st.line_chart(trend.set_index('Semester')['GPA'], color="#88A2FF")
