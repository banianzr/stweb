import streamlit as st

st.title("AI 应用演示")
st.write("搜索、文档解析、问答和智能体")

# 快速入口按钮
if st.button("🔍 搜索"):
    st.switch_page("search/search.py")
if st.button("📉 问数"):
    st.switch_page("qabot/statistical_bot.py")
# if st.button("📏 问策"):
#     st.switch_page("qabot/policy_bot.py")
