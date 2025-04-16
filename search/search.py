import streamlit as st
import validators

from urllib.parse import urlparse
from search.searxng_search import build_query_target_domain, web_search, sort_results

st.title("AI 应用演示")
st.write("联网搜索")
user_input =  st.text_input("请输入搜索内容")

col1, col2 = st.columns([3, 9])
with col1:
    option = st.selectbox(
        "搜索特定网站",
        ("不限", "深圳市科技创新局", "其它"),
        1
    )
with col2:
    if option == "不限":
        target_domain = ""
    elif option == "深圳市科技创新局":
        target_domain = "stic.sz.gov.cn"
    if option == "其它":
        target_website = st.text_input(
            "请输入网址", placeholder="请输入网址", 
            label_visibility="hidden"
        )
        if target_website:
            # 验证输入的 URL 是否有效
            if validators.url(target_website):
                # 解析 URL 以提取域名
                parsed_url = urlparse(target_website)
                target_domain = parsed_url.netloc
            else:
                st.error("请输入有效的网址。")
    
if st.button("搜索"):
    if not user_input:
        st.error("请输入搜索关键词")
        st.stop()
    else: 
        valid_input = user_input.replace(" ", "+") if " " in user_input else user_input
        query_input = build_query_target_domain(valid_input, target_domain) if target_domain else valid_input
        results = web_search(query_input)["results"]
        results = sort_results(results, sort_by='publishedDate')
        print(results)
        if results:
            # results = sort_results(results)
            st.subheader(f"共找到 {len(results)} 条结果")
            for result in results:
                st.markdown(f"#### [{result['title']}]({result['url']})")
                st.write(f"摘要: {result['content']}")
                st.write(f"发布日期: {result['publishedDate']}")
                st.markdown("---")