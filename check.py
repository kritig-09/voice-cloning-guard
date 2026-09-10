import os, re
dashboard_file = 'dashboard.py' if os.path.exists('dashboard.py') else 'dashboard/dashboard.py'
app_file = 'app.py' if os.path.exists('app.py') else 'dashboard/app.py'

try:
    with open(dashboard_file, 'r', encoding='utf-8') as f: d_content = f.read()
except:
    d_content = ''

try:
    with open(app_file, 'r', encoding='utf-8') as f: a_content = f.read()
except:
    a_content = ''

print('Dashboard File:', dashboard_file)
print('App File:', app_file)

print('DASHBOARD CHECKS:')
print('analyze_file:', 'PASS' if 'analyze_file' in d_content else 'FAIL')
print('API_URL:', 'PASS' if 'API_URL' in d_content else 'FAIL')
print('st.file_uploader:', 'PASS' if 'st.file_uploader' in d_content else 'FAIL')
print('st.session_state:', 'PASS' if 'st.session_state' in d_content else 'FAIL')
print('try/except:', 'PASS' if 'try:' in d_content and 'except' in d_content else 'FAIL')

print('APP CHECKS:')
print('PREDICT_ENDPOINT:', 'PASS' if 'PREDICT_ENDPOINT' in a_content else 'FAIL')
print('HEALTH_ENDPOINT:', 'PASS' if 'HEALTH_ENDPOINT' in a_content else 'FAIL')

m_d = re.search(r'^ {4}(\"\"\"|\'\'\')', d_content, re.MULTILINE)
m_a = re.search(r'^ {4}(\"\"\"|\'\'\')', a_content, re.MULTILINE)
print('Dashboard Markdown strings (4 spaces):', 'FAIL' if m_d else 'PASS')
print('App Markdown strings (4 spaces):', 'FAIL' if m_a else 'PASS')

imports = ['requests', 'streamlit', 'pandas', 'datetime', 'os']
for imp in imports:
    found = re.search(rf'^(import {imp}|from {imp} )', d_content, re.MULTILINE)
    print(f'Import {imp}:', 'PASS' if found else 'FAIL')
