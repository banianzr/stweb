import streamlit as st
# from streamlit_option_menu import option_menu

from dotenv import load_dotenv
load_dotenv()

# 设置页面配置
st.set_page_config(page_title="AI 应用演示", layout="wide")

# 初始化 session_state 来跟踪当前页面
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# 定义页面
home = st.Page("home.py", title="🏠 首页")
search = st.Page("search/search.py", title="🔍 联网搜索")
# doc_parser = st.Page("document_parser/document_parser.py", title="📄 文件解析")
statistical_bot = st.Page("qabot/statistical_bot.py", title="📉 问数")
# policy_bot = st.Page("qabot/policy_bot.py", title="📏 问策")

# 将所有页面传递给 st.navigation
pg = st.navigation([home, search, statistical_bot])

pg.run()

