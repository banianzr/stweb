import io, os, requests, sys
import streamlit as st
import pandas as pd
import numpy as np

from contextlib import redirect_stdout
from datetime import datetime

from document_parser.document_upload import save_to_tmp_dir
from utils.logging import get_logger
logger = get_logger("simple_bot")

# 提取多个文件信息
def extract_file_info(file_paths):
    info = ""
    for i, file_path in enumerate(file_paths, start=1):
        df = pd.read_excel(file_path)
        columns_info = [f"{col} ({df[col].dtype})" for col in df.columns]
        info += f"# 文件{i}:\n"
        info += f"    - 总行数: {df.shape[0]}\n"
        info += f"    - 列名及类型: {', '.join(columns_info)}\n"
    return info

# 获取LLM分析，处理工具调用
def get_llm_analysis(dialog_history, file_paths, model_name="qwen2.5:latest"):
    try:
        data = {
            "model": model_name,
            "messages": dialog_history,
            "stream": False
        }
        headers = {
            "Content-Type": "application/json"
        }
        # 记录请求输入
        logger.info(f"Request Input: {data}")
        response = requests.post(
            f"{os.getenv('LLM_HOST')}/v1/chat/completions", 
            json=data, headers=headers
        )
        response.raise_for_status()
        response_data = response.json()
        # 记录请求输出
        logger.info(f"Request Output: {response_data}")

        tool_calls = extract_tool_calls(response_data)
        if tool_calls:
            for tool_call in tool_calls:
                result = execute_tool_call(tool_call, file_paths)
                if result["success"]:
                    # 将执行结果添加到对话历史中
                    result_text = "\n".join(result["text_output"])
                    for name, frame in result["dataframes"].items():
                        csv_str = frame.to_csv(sep='\t', na_rep='nan')
                        result_text += f"\n{name}:\n{csv_str}"
                    dialog_history.append({"role": "function_call", "name": tool_call["name"], "parameters": {"result": result_text}})
                    # 再次请求模型获取最终回答
                    return get_llm_analysis(dialog_history, model_name, api_base, file_paths)
                else:
                    return result["error"], None

        response_text = response_data["message"]["content"]
        return None, response_text
    except requests.exceptions.RequestException as e:
        return f"请求失败: {e}", None
    except Exception as e:
        return str(e), None

st.title("AI 应用演示")
st.write("📉 问数")

# 初始化聊天历史（在会话状态中保存）
chat_history = st.session_state.get("chat_history", [])
# 显示聊天历史
for msg in st.session_state.chat_history:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

user_input = st.chat_input(
    placeholder="请上传文件并输入您的问题...",
    # accept_file="multiple",
    accept_file=True,
    file_type=["xlsx", "xls", "csv"]
)
UPLOAD_DIR = os.getenv("TMP_DIR")
if user_input and user_input.text:
    st.markdown(user_input.text)
    uploaded_files = user_input.get("files", [])
    logger.info(f"user upload files: {uploaded_files}")
    if uploaded_files:
        with st.spinner("正在上传文件..."):
            file_list = save_to_tmp_dir(uploaded_files)

        # 调用 LLM 进行解析
        base_url = os.getenv("LLM_HOST")
        # 系统提示词
        system_prompt = """你是一个专业的数据分析助手。用户会上传 Excel 文件并提出问题。你需要根据已知情况判断是否可以直接回答问题，若不能直接回答，则生成 Python 代码对文件进行分析，并调用代码执行工具执行代码。请直接根据代码执行结果进行回答，不要呈现代码生成和执行的中间过程。确保代码使用提供的 file_paths 字典来访问文件，字典的键是文件名，值是文件的本地路径。"""

        # 提取文件信息
        file_info = extract_file_info(file_list)
        # 构建完整的用户提示词
        num_files = len(file_list)
        file_path_str = ", ".join(file_list)
        full_user_prompt = f"我有 {num_files} 个文件，文件地址为 {file_path_str}。其中：\n{file_info}\n我的问题是: {user_query}"

        # 将完整的用户提示词添加到对话历史
        st.session_state.dialog_history.append({"role": "user", "content": full_user_prompt})

        # 显示加载状态
        with st.spinner("正在分析数据..."):
            # 获取LLM分析
            error, llm_response = get_llm_analysis(st.session_state.dialog_history, model_name, api_base, file_paths)

            if error:
                st.error(error)
                return

            # 将LLM响应添加到对话历史
            st.session_state.dialog_history.append({"role": "assistant", "content": llm_response})

            # 显示LLM响应
            st.subheader("LLM分析结果")
            st.markdown(llm_response)
