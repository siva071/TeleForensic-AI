import streamlit as st
import pandas as pd

from datetime import datetime
from modules.data_loader import (
  load_excel, clean_dataframe, 
  detect_file_type, get_file_summary)
from modules.pattern_engine import (
  analyze_patterns, findings_to_text)
from modules.suspicion_scorer import (
  calculate_scores, scores_to_text)
from modules.network_graph import build_graph
from modules.tower_map import build_map
from modules.chatbot import (
  get_ai_response, format_history)
from modules.correlation_engine import (
  correlate_datasets, correlation_to_text)
from modules.report_generator import generate_report


# Page config
st.set_page_config(
  page_title="TeleForensic AI",
  page_icon="🔍",
  layout="wide")

# Initialize session state
if 'logged_in' not in st.session_state:
  st.session_state.logged_in = False
if 'page' not in st.session_state:
  st.session_state.page = 'login'
if 'users' not in st.session_state:
  st.session_state.users = {
    'admin': {
      'password': 'admin123',
      'full_name': 'Administrator',
      'role': 'Administrator'
    }
  }
if 'chat_history' not in st.session_state:
  st.session_state.chat_history = []
if 'analysis_done' not in st.session_state:
  st.session_state.analysis_done = False
if 'report_downloaded' not in st.session_state:
  st.session_state.report_downloaded = False
if 'cases' not in st.session_state:
  st.session_state.cases = {}

def show_login():
  """Display login page"""
  col1, col2, col3 = st.columns([1,2,1])
  with col2:
    st.markdown("# 🔍 TeleForensic AI")
    st.markdown("### Police Telecom Forensics Platform")
    st.markdown("---")
    
    username = st.text_input("Username")
    password = st.text_input("Password", 
                            type="password")
    
    col_a, col_b = st.columns(2)
    with col_a:
      if st.button("🔐 Login", 
                  use_container_width=True,
                  type="primary"):
        if username in st.session_state.users:
          stored = st.session_state.users[username]
          if stored['password'] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = stored['role']
            st.session_state.full_name = stored['full_name']
            st.rerun()
          else:
            st.error("❌ Invalid password")
        else:
          st.error("❌ User not found")
    
    with col_b:
      if st.button("📝 Register",
                  use_container_width=True):
        st.session_state.page = 'register'
        st.rerun()

def show_register():
  """Display registration page"""
  col1, col2, col3 = st.columns([1,2,1])
  with col2:
    st.markdown("# 📝 Create Account")
    st.markdown("### TeleForensic AI")
    st.markdown("---")
    
    full_name = st.text_input("Full Name")
    username = st.text_input("Username")
    password = st.text_input("Password",
                            type="password")
    confirm = st.text_input("Confirm Password",
                           type="password")
    role = st.selectbox("Role", [
      "Investigator",
      "Analyst", 
      "Supervisor"])
    
    col_a, col_b = st.columns(2)
    with col_a:
      if st.button("✅ Register",
                  use_container_width=True,
                  type="primary"):
        if not all([full_name, username, 
                    password, confirm]):
          st.error("All fields required")
        elif password != confirm:
          st.error("Passwords do not match")
        elif len(password) < 6:
          st.error("Password min 6 characters")
        elif username in st.session_state.users:
          st.error("Username already exists")
        else:
          st.session_state.users[username] = {
            'password': password,
            'full_name': full_name,
            'role': role
          }
          st.success("Account created! Please login.")
          st.session_state.page = 'login'
          st.rerun()
    
    with col_b:
      if st.button("← Back to Login",
                  use_container_width=True):
        st.session_state.page = 'login'
        st.rerun()

def show_main_app():
  """Main application interface"""
  # SIDEBAR
  with st.sidebar:
    st.markdown("## 🔍 TeleForensic AI")
    st.markdown(f"👤 **{st.session_state.get('full_name')}**")
    st.markdown(f"🎯 {st.session_state.get('role')}")
    st.divider()
    
    api_key = st.text_input(
      "🔑 Gemini API Key",
      type="password",
      key="api_key")
    st.caption("Get free key: aistudio.google.com")
    st.divider()
    
    st.markdown("### 📁 Upload Investigation Files")
    cdr_file = st.file_uploader(
      "CDR File (Required)", 
      type=['xlsx','csv'])
    tower_file = st.file_uploader(
      "Tower Dump (Optional)", 
      type=['xlsx','csv'])
    ipdr_file = st.file_uploader(
      "IPDR File (Optional)", 
      type=['xlsx','csv'])
    
    st.divider()
    
    if st.button("🔍 Analyze Data", 
                 type="primary",
                 use_container_width=True):
      if cdr_file is None:
        st.error("CDR file required")
      else:
        with st.spinner("Analyzing..."):
          
          cdr_df = clean_dataframe(
                     load_excel(cdr_file))
          tower_df = clean_dataframe(
                       load_excel(tower_file)) \
                     if tower_file else None
          ipdr_df = clean_dataframe(
                      load_excel(ipdr_file)) \
                    if ipdr_file else None
          
          patterns = analyze_patterns(cdr_df)
          findings_text = findings_to_text(
                            patterns, cdr_df)
          
          dfs = {'cdr': cdr_df, 
                 'tower': tower_df,
                 'ipdr': ipdr_df}
          correlation = correlate_datasets(dfs)
          correlation_text = correlation_to_text(
                               correlation)
          
          scores = calculate_scores(patterns)
          scores_text = scores_to_text(scores)
          
          graph_path = build_graph(cdr_df, scores)
          map_path = build_map(tower_df, scores) \
                     if tower_df is not None else None
          
          datasets_loaded = sum([
            1 if cdr_df is not None else 0,
            1 if tower_df is not None else 0,
            1 if ipdr_df is not None else 0])
          
          st.session_state.update({
            'cdr_df': cdr_df,
            'tower_df': tower_df,
            'ipdr_df': ipdr_df,
            'patterns': patterns,
            'findings_text': findings_text,
            'scores': scores,
            'scores_text': scores_text,
            'correlation_text': correlation_text,
            'graph_path': graph_path,
            'map_path': map_path,
            'datasets_loaded': datasets_loaded,
            'analysis_done': True,
            'file_context': 
              get_file_summary(cdr_df, 'CDR')
          })
          st.success("✅ Analysis complete!")
    
    st.divider()
    if st.button("🚪 Logout", 
                 use_container_width=True):
      for key in list(st.session_state.keys()):
        del st.session_state[key]
      st.rerun()
    
    st.divider()
    st.markdown("### 📁 Case Management")
    case_name = st.text_input("Case Name (e.g., Case_001)")
    if st.button("💾 Save Case"):
      if case_name and st.session_state.analysis_done:
        st.session_state.cases[case_name] = {
          'scores': st.session_state.scores,
          'patterns': st.session_state.patterns,
          'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        st.success(f"✅ {case_name} saved!")
    
    if st.session_state.cases:
      selected_case = st.selectbox("Load Case", list(st.session_state.cases.keys()))
      if st.button("📂 Load Case"):
        case = st.session_state.cases[selected_case]
        st.session_state.scores = case['scores']
        st.session_state.patterns = case['patterns']
        st.session_state.analysis_done = True
        st.success(f"✅ {selected_case} loaded!")
        st.rerun()

  # MAIN TABS
  tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
    "📊 Dashboard",
    "🔍 Patterns", 
    "🕸️ Network",
    "🗺️ Tower Map",
    "🤖 AI Chatbot",
    "🔎 Compare Numbers",
    "📅 Timeline"])

  # TAB 1 — Dashboard
  with tab1:
    if not st.session_state.analysis_done:
      st.info("Upload CDR file and click Analyze")
    else:
      scores = st.session_state.scores
      cdr_df = st.session_state.cdr_df
      
      high_risk = [s for s in scores 
                   if s['label']=='HIGH RISK']
      
      c1,c2,c3,c4 = st.columns(4)
      c1.metric("Total Numbers", 
                 len(scores))
      c2.metric("🔴 HIGH RISK", 
                 len(high_risk))
      c3.metric("Total Calls", 
                 len(cdr_df))
      c4.metric("Datasets Loaded",
                 st.session_state.datasets_loaded)
      
      st.markdown("### Suspicion Scores")
      import pandas as pd
      scores_df = pd.DataFrame(scores)
      
      def color_rows(row):
        if row['label'] == 'HIGH RISK':
          return ['background-color: #ff4444; color: white'] * len(row)
        elif row['label'] == 'Medium':
          return ['background-color: #ffa500; color: white'] * len(row)
        else:
          return ['background-color: #44bb44; color: white'] * len(row)
      
      st.dataframe(
        scores_df.style.apply(
          color_rows, axis=1),
        use_container_width=True)
      
      import plotly.express as px
      top5 = scores_df.head(5)
      colors = {'HIGH RISK':'red',
                'Medium':'orange',
                'Low':'green'}
      fig = px.bar(
        top5,
        x='number',
        y='score',
        color='label',
        color_discrete_map=colors,
        title='Top 5 Suspicious Numbers')
      fig.update_xaxes(type='category')
      st.plotly_chart(fig, 
                      use_container_width=True)
      
      if st.button("📥 Download Report"):
        path = generate_report(
          patterns, scores, correlation, 'report')
        with open(path, 'rb') as f:
          st.download_button(
            "📥 Download Excel Report",
            f.read(),
            file_name=path,
            mime='application/vnd.ms-excel')
        st.session_state.report_downloaded = True

  # TAB 2 — Patterns
  with tab2:
    if not st.session_state.analysis_done:
      st.info("Analyze data first")
    else:
      patterns = st.session_state.patterns
      cdr_df = st.session_state.cdr_df
      
      st.divider()
      st.subheader("🚔 Select Investigation Type")
      
      case_type = st.selectbox(
        "What type of case are you investigating?",
        [
          "Select Case Type...",
          "💊 Drug Network",
          "💣 Terror Module", 
          "👤 Kidnapping/Missing Person",
          "💰 Financial Fraud",
          "🔫 Organized Crime/Gang",
          "📱 Cyber Crime",
          "🔍 General Investigation"
        ])
      
      if case_type != "Select Case Type...":
        if case_type == "💊 Drug Network":
          st.info("""
    🎯 Drug Network Investigation Mode
    
    Key indicators to look for:
    • Short calls < 30 sec = order signals
    • Night activity = covert operations  
    • Sequential SIMs = dealer hierarchy
    • Tower clusters = distribution points
    
    AI will now focus on these patterns.
    """)
          st.session_state.focus_mode = 'drug'
        
        elif case_type == "💣 Terror Module":
          st.info("""
    🎯 Terror Module Investigation Mode
    
    Key indicators:
    • VPN/Tor/Dark web usage in IPDR
    • Encrypted app usage (Telegram)
    • Sudden call silence = operation planned
    • Sequential SIMs = cell members
    
    Check IPDR tab for suspicious sites.
    """)
          st.session_state.focus_mode = 'terror'
        
        elif case_type == "👤 Kidnapping/Missing Person":
          st.info("""
    🎯 Kidnapping Investigation Mode
    
    Key steps:
    • Check last tower ping of victim
    • Find suspect numbers at same tower
    • Timeline analysis around 
      disappearance time
    • Cross-check caller locations
    
    Use Tower Map + Compare tabs.
    """)
          st.session_state.focus_mode = 'kidnap'
        
        elif case_type == "💰 Financial Fraud":
          st.info("""
    🎯 Financial Fraud Investigation Mode
    
    Key indicators:
    • Many different numbers calling 
      same receiver (victims)
    • Sequential SIMs = fraud gang
    • Short repeated calls = script reading
    • Bulk outgoing calls pattern
    
    Check Network Graph for hub numbers.
    """)
          st.session_state.focus_mode = 'fraud'
        
        elif case_type == "🔫 Organized Crime/Gang":
          st.info("""
    🎯 Organized Crime Investigation Mode
    
    Key indicators:
    • Group calling patterns
    • Sequential SIM series
    • Same tower usage
    • Coordinated timing
    
    Look for gang structure in Network Graph.
    """)
          st.session_state.focus_mode = 'gang'
        
        elif case_type == "📱 Cyber Crime":
          st.info("""
    🎯 Cyber Crime Investigation Mode
    
    Key indicators:
    • Suspicious IPDR patterns
    • Dark web activity
    • Unusual data usage
    • Technical indicators
    
    Focus on IPDR and technical analysis.
    """)
          st.session_state.focus_mode = 'cyber'
        
        else:
          st.info("""
    🎯 General Investigation Mode
    
    Standard forensic analysis across all patterns.
    No specific focus - comprehensive review.
    """)
          st.session_state.focus_mode = 'general'
      
      st.subheader("🗓️ Filter by Date Range")
      col1, col2 = st.columns(2)
      with col1:
        start_date = st.date_input("From Date")
      with col2:
        end_date = st.date_input("To Date")

      if st.button("Apply Filter"):
        # Convert date columns if needed
        if 'call_datetime' not in cdr_df.columns and 'timestamp' in cdr_df.columns:
          cdr_df['call_datetime'] = pd.to_datetime(cdr_df['timestamp'])
        elif 'call_datetime' not in cdr_df.columns and 'call_datetime' in cdr_df.columns:
          cdr_df['call_datetime'] = pd.to_datetime(cdr_df['call_datetime'])
          
        filtered_df = cdr_df[
          (cdr_df['call_datetime'].dt.date >= start_date) &
          (cdr_df['call_datetime'].dt.date <= end_date)]
        filtered_patterns = analyze_patterns(filtered_df)
        st.session_state.filtered_patterns = filtered_patterns
        st.success(
          f"Showing {len(filtered_df)} calls between {start_date} and {end_date}")
        st.rerun()
        return
      
      st.subheader("📞 Frequent Numbers")
      if 'frequent' in patterns:
        st.dataframe(patterns['frequent'],
                     use_container_width=True)
      
      st.subheader("🌙 Night Calls (11pm-5am)")
      if 'night_calls' in patterns:
        st.dataframe(patterns['night_calls'],
                     use_container_width=True)
      
      st.subheader("⚡ Short Calls (<30 sec)")
      if 'short_calls' in patterns:
        st.dataframe(patterns['short_calls'],
                     use_container_width=True)
      
      st.subheader("📵 Missed Calls")
      if 'missed_calls' in patterns:
        st.dataframe(patterns['missed_calls'],
                     use_container_width=True)
      
      st.subheader("🔢 Sequential SIM Detection")
      if patterns.get('sequential'):
        for series in patterns['sequential']:
          st.warning(
            f"⚠️ Series: {' → '.join(map(str,series))}")
      else:
        st.success("✅ No sequential series found")

  # TAB 3 — Network Graph
  with tab3:
    if not st.session_state.analysis_done:
      st.info("Analyze data first")
    elif st.session_state.graph_path:
      html = open(
        st.session_state.graph_path).read()
      st.components.v1.html(html, height=600)
      st.caption(
        "🔴 HIGH RISK  🟠 Medium  🟢 Low")
    else:
      st.warning("Could not build graph")

  # TAB 4 — Tower Map
  with tab4:
    if st.session_state.get('map_path'):
      html = open(
        st.session_state.map_path).read()
      st.components.v1.html(html, height=500)
    else:
      st.info(
        "Upload Tower Dump file to see map")

  # TAB 6 — Compare Numbers
  with tab6:
    st.header("🔎 Compare Two Numbers")
    
    if not st.session_state.analysis_done:
      st.info("Analyze data first")
    else:
      cdr_df = st.session_state.cdr_df
      
      col1, col2 = st.columns(2)
      with col1:
        num1 = st.text_input("Number 1")
      with col2:
        num2 = st.text_input("Number 2")
      
      if st.button("Compare") and num1 and num2:
        # Calls between these two numbers
        calls_1to2 = cdr_df[
          (cdr_df['caller_number']==num1) & 
          (cdr_df['receiver_number']==num2)]
        
        calls_2to1 = cdr_df[
          (cdr_df['caller_number']==num2) & 
          (cdr_df['receiver_number']==num1)]
        
        # Same tower same time check
        same_location = []
        if st.session_state.get('tower_df') is not None:
          tower_df = st.session_state.tower_df
          towers_1 = tower_df[tower_df['phone_number']==num1]
          towers_2 = tower_df[tower_df['phone_number']==num2]
          
          for _, r1 in towers_1.iterrows():
            for _, r2 in towers_2.iterrows():
              if r1['tower_id'] == r2['tower_id']:
                time_diff = abs(
                  (r1['datetime'] - r2['datetime'])
                  .total_seconds() / 60)
                if time_diff <= 60:
                  same_location.append({
                    'tower': r1['tower_id'],
                    'area': r1['area_name'],
                    'time_diff_mins': round(time_diff, 1)
                  })
        
        # Show results
        st.subheader("📊 Comparison Results")
        
        c1, c2, c3 = st.columns(3)
        c1.metric(
          f"{num1} → {num2}", 
          f"{len(calls_1to2)} calls")
        c2.metric(
          f"{num2} → {num1}", 
          f"{len(calls_2to1)} calls")
        c3.metric(
          "Same Location Events",
          len(same_location))
        
        if len(calls_1to2) > 0 or len(calls_2to1) > 0:
          st.error(
            f"⚠️ CONNECTED: These numbers contacted each other {len(calls_1to2)+len(calls_2to1)} times!")
        else:
          st.success("No direct contact found")
        
        if same_location:
          st.warning("📍 Same Location Detected!")
          st.dataframe(pd.DataFrame(same_location))
        
        if len(calls_1to2) > 0:
          st.subheader(f"Calls: {num1} → {num2}")
          st.dataframe(calls_1to2)
        
        if len(calls_2to1) > 0:
          st.subheader(f"Calls: {num2} → {num1}")
          st.dataframe(calls_2to1)

  # TAB 7 — Timeline
  with tab7:
    st.header("📅 Activity Timeline")
    
    if not st.session_state.analysis_done:
      st.info("Analyze data first")
    else:
      cdr_df = st.session_state.cdr_df
      scores = st.session_state.scores
      
      # Select number to view timeline
      all_numbers = list(cdr_df['caller_number'].unique())
      selected = st.selectbox("Select Number", all_numbers)
      
      # Filter calls for selected number
      number_calls = cdr_df[
        (cdr_df['caller_number']==selected) |
        (cdr_df['receiver_number']==selected)
      ].copy()
      
      # Convert date columns if needed
      if 'call_datetime' not in number_calls.columns and 'timestamp' in number_calls.columns:
        number_calls['call_datetime'] = pd.to_datetime(number_calls['timestamp'])
      elif 'call_datetime' not in number_calls.columns and 'call_datetime' in number_calls.columns:
        number_calls['call_datetime'] = pd.to_datetime(number_calls['call_datetime'])
          
      number_calls['hour'] = number_calls['call_datetime'].dt.hour
      number_calls['date'] = number_calls['call_datetime'].dt.date
      
      # Hourly activity chart
      import plotly.express as px
      hourly = number_calls.groupby('hour').size().reset_index(name='calls')
      
      fig1 = px.bar(
        hourly, x='hour', y='calls',
        title=f'Hourly Activity: {selected}',
        color='calls',
        color_continuous_scale='Reds')
      fig1.add_vrect(
        x0=23, x1=24,
        fillcolor='red', opacity=0.2,
        annotation_text="Night")
      fig1.add_vrect(
        x0=0, x1=5,
        fillcolor='red', opacity=0.2,
        annotation_text="Night")
      st.plotly_chart(fig1, use_container_width=True)
      
      # Daily activity chart
      daily = number_calls.groupby('date').size().reset_index(name='calls')
      
      fig2 = px.line(
        daily, x='date', y='calls',
        title=f'Daily Activity: {selected}',
        markers=True)
      st.plotly_chart(fig2, use_container_width=True)
      
      # Call type breakdown
      if 'call_type' in number_calls.columns:
        call_types = number_calls['call_type'].value_counts()
        fig3 = px.pie(
          values=call_types.values,
          names=call_types.index,
          title='Call Type Breakdown',
          color_discrete_map={
            'outgoing':'blue',
            'incoming':'green',
            'missed':'red'})
        st.plotly_chart(fig3, use_container_width=True)
  with tab5:
    st.markdown("### 🤖 TeleForensic AI Chatbot")
    
    if not st.session_state.get('api_key'):
      st.warning(
        "Enter Gemini API key in sidebar")
      st.stop()
    
    # FILE UPLOAD INSIDE CHAT
    chat_file = st.file_uploader(
      "📎 Upload CSV/Excel directly for instant analysis",
      type=['csv','xlsx'],
      key='chat_upload')
    
    if chat_file is not None:
      if st.session_state.get(
           'last_chat_file') != chat_file.name:
        
        st.session_state.last_chat_file = \
          chat_file.name
        
        with st.spinner("Analyzing file..."):
          df = load_excel(chat_file)
          df = clean_dataframe(df)
          
          file_summary = get_file_summary(
                           df, chat_file.name)
          chat_patterns = analyze_patterns(df)
          chat_findings = findings_to_text(
                            chat_patterns, df)
          chat_scores = calculate_scores(
                          chat_patterns)
          chat_scores_text = scores_to_text(
                               chat_scores)
          
          st.session_state.chat_file_context = \
            file_summary
          st.session_state.chat_findings = \
            chat_findings
          st.session_state.chat_scores_text = \
            chat_scores_text
          
          auto_response = get_ai_response(
            user_message=
              "Analyze this file and give complete summary",
            file_context=file_summary,
            findings_text=chat_findings,
            scores_text=chat_scores_text,
            chat_history="",
            api_key=st.session_state.api_key)
          
          st.session_state.chat_history.append({
            'role': 'user',
            'content': f'📎 Uploaded: {chat_file.name}'})
          st.session_state.chat_history.append({
            'role': 'assistant',
            'content': auto_response})
          
          st.rerun()
    
    # EXAMPLE BUTTONS
    st.markdown("**Quick Questions:**")
    cols = st.columns(3)
    questions = [
      "Who is most suspicious?",
      "Investigation leads?",
      "Night activity?",
      "Sequential SIMs?",
      "Summarize findings",
      "అనుమానాస్పద నంబర్లు?",
      "IPDR suspicious data?",
      "VPN usage in IPDR?",
      "Dark web activity?",
      "Tower locations?",
      "Same tower meetings?"
    ]
    
    for i, q in enumerate(questions):
      with cols[i % 3]:
        if st.button(q, 
                     use_container_width=True,
                     key=f"btn_{i}"):
          st.session_state.quick_q = q
    
    # CHAT DISPLAY
    for msg in st.session_state.chat_history:
      with st.chat_message(msg['role']):
        st.write(msg['content'])
    
    # CHAT INPUT
    user_input = st.chat_input(
      "Ask anything about the investigation...")
    
    if st.session_state.get('quick_q'):
      user_input = st.session_state.quick_q
      st.session_state.quick_q = None
    
    if user_input:
      st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input})
      
      # Detect if user is asking about specific data types
      user_input_lower = user_input.lower()
      is_ipdr_query = 'ipdr' in user_input_lower
      is_tower_query = 'tower' in user_input_lower
      is_cdr_query = 'cdr' in user_input_lower
      
      if is_ipdr_query and st.session_state.get('ipdr_df') is not None:
        # Use IPDR-specific context for IPDR queries
        ipdr_summary = get_file_summary(
          st.session_state.ipdr_df, 'IPDR')
        ipdr_patterns = analyze_patterns(
          st.session_state.ipdr_df)
        ipdr_findings = findings_to_text(
          ipdr_patterns, st.session_state.ipdr_df)
        ipdr_scores = calculate_scores(ipdr_patterns)
        ipdr_scores_text = scores_to_text(ipdr_scores)
        
        file_ctx = ipdr_summary
        findings = ipdr_findings
        scores_t = ipdr_scores_text
        
      elif is_tower_query and st.session_state.get('tower_df') is not None:
        # Use Tower-specific context for tower queries
        tower_summary = get_file_summary(
          st.session_state.tower_df, 'Tower Dump')
        tower_patterns = analyze_patterns(
          st.session_state.tower_df)
        tower_findings = findings_to_text(
          tower_patterns, st.session_state.tower_df)
        tower_scores = calculate_scores(tower_patterns)
        tower_scores_text = scores_to_text(tower_scores)
        
        file_ctx = tower_summary
        findings = tower_findings
        scores_t = tower_scores_text
        
      else:
        # Use regular context for other queries
        file_ctx = st.session_state.get(
          'chat_file_context') or \
          st.session_state.get('file_context','')
        
        findings = st.session_state.get(
          'chat_findings') or \
          st.session_state.get('findings_text','')
        
        scores_t = st.session_state.get(
          'chat_scores_text') or \
          st.session_state.get('scores_text','')
      
      history = format_history(
        st.session_state.chat_history[-6:])
      
      with st.spinner("Analyzing..."):
        response = get_ai_response(
          user_message=user_input,
          file_context=file_ctx,
          findings_text=findings,
          scores_text=scores_t,
          chat_history=history,
          api_key=st.session_state.api_key)
      
      st.session_state.chat_history.append({
        'role': 'assistant',
        'content': response})
      
      st.rerun()

# Main flow
if not st.session_state.logged_in:
  if st.session_state.page == 'register':
    show_register()
  else:
    show_login()
else:
  show_main_app()
