import os, requests
import json

import pandas as pd
import numpy as np
import streamlit as st

from datetime import datetime
from document_parser.document_upload import save_to_tmp_dir
from document_parser.excel_parser import get_topk_rows_from_file, detect_headers_llm
from tools.code_generator import code_generator_tool
from tools.code_executor import code_executor_tool

from utils.logging import get_logger
logger = get_logger("statistical_bot")

def filter_and_join(tup, sep='_'):
    # 过滤掉 'Unnamed: x_level_y' 形式的值
    filtered_tup = [item for item in tup if not str(item).startswith('Unnamed:')]
    # 用连接符拼接剩余元素
    return sep.join(filtered_tup)

st.title("AI 应用演示")
st.write("📉 问数")

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
        file_headers = {}
        df_info = {}
        with st.spinner("正在读取文件..."):
            for f in file_list:
                df_info[f] = []
                data_sample = get_topk_rows_from_file(f"{f}")
                file_headers[f] = detect_headers_llm(data_sample)
                for k, v in file_headers[f].items():
                    # print(f"file name: {f}, key: {k}, value: {v}")
                    sheet_headers = v
                    if f.endswith(".xlsx") or f.endswith(".xls"):
                        df = pd.read_excel(f"{f}", sheet_name=k, header=v)
                        # print(df.columns)
                        # 获取列名
                        columns = list(df.columns)
                        is_multiindex = False
                        if len(v) > 1:
                            # 转换为字符串列表
                            columns = [filter_and_join(tup) for tup in columns]
                            is_multiindex = True
                        # if len(df) > 20:
                        df_info[f].append({
                            "sheet_name": k,
                            "header": v,
                            "multiindex": is_multiindex,
                            "column_info(merged)": columns,
                            "data_len": len(df)
                        })
                        # else :
                        #     df_info[f].append({
                        #         "sheet_name": k,
                        #         "header": v,
                        #         "multiindex": is_multiindex,
                        #         "column_info(merged)": columns,
                        #         "data_len": len(df),
                        #         "data": df.values.tolist()
                        #     })
                    elif f.endswith(".csv"):
                        df = pd.read_csv(f"{UPLOAD_DIR}/{f}")
                        # if len(df) > 20:
                        df_info[f].append({
                            "sheet_name": None,
                            "header": 0,
                            "multiindex": False,
                            "column_info(merged)": list(df.columns),
                            "data_len": len(df)
                        })
                        # else :
                        #     df_info[f].append({
                        #         "sheet_name": k,
                        #         "header": v,
                        #         "multiindex": is_multiindex,
                        #         "column_info(merged)": columns,
                        #         "data_len": len(df),
                        #         "data": df.values.tolist()
                        #     })
        with st.spinner("正在分析文件..."):
            # 调用 LLM 进行解析
            base_url = os.getenv("LLM_HOST")

            tools=[{
                "type": "function",
                "function":{
                    "name": "code_generator_tool",
                    "description": "根据用户问题、文件路径、文件信息和模型名称生成python代码",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "用户问题"
                            },
                            "filepath": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "file_structure": {
                                "type": "object",
                                "description": "文件信息"
                            }
                        },
                        "required": ["query", "filepath", "file_structure"]
                    }
                }},{
                "type": "function",
                "function":{
                    "name": "code_executor_tool",
                    "description": "执行python代码并返回结果",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "待执行的python代码"
                            }
                        },
                        "required": ["code"]
                    }
                }}
            ]

            sys_prompt = f"""
            你是一个 Excel 数据分析师，根据用户提供的 Excel 文件和文件结构信息回答用户的问题。你需要根据已知情况判断是否可以直接回答问题，若不能直接回答，则使用提供的工具来处理 Excel 文件并回答问题。

            可用工具及调用方法：
            1. code_generator_tool: 
                - 描述: 使用此工具根据用户问题、文件路径、文件信息生成 Python 代码
            2. code_executor_tool:
                - 描述: 使用此工具执行 Python 代码
            
            但需要调用工具时，请务必确保返回的工具参数满足JSON规范
            """

            user_prompt = f"""
            用户问题: {user_input.text}
            Excel文件路径: {file_list}
            Excel文件信息: {df_info}
            """

            messages = [
                {"role":"system", "content": sys_prompt},{"role":"user", "content": user_prompt}
            ]
            data = {
                "model": "qwen2.5:latest",
                "messages": messages,
                "tools": tools,
                "temperature": 0.1
            }
            response = requests.post(f"{base_url}/v1/chat/completions", json=data)
            response_json = response.json()
            print(response_json)

            finish_reason = response_json['choices'][0]['finish_reason']
            if finish_reason == "stop":
                content = response_json['choices'][0]['message'].get('content', '')
                if "<tool_call>" in content:
                    start_index = content.find('<tool_call>\n')
                    end_index = content.find('\n</tool_call>')
                    logger.debug(f"tool call in content.\nstart_index: {start_index}, end_index: {end_index}")
                    if start_index != -1 and end_index != -1:
                        tool_call_str = content[start_index + len('<tool_call>'):end_index].strip().replace("True", "true").replace("False", "false")
                        logger.info(f"Extracted tool_call_str: {tool_call_str}")
                        try:
                            tool_call_json = json.loads(tool_call_str)
                            logger.info(f"Parsed tool_call name: {tool_call_json['name']}")
                            tool_name = tool_call_json['name']
                            tool_args = tool_call_json['arguments']
                            if isinstance(tool_args, str):
                                tool_args = json.loads(tool_args)
                            if tool_name == "code_generator_tool":
                                query = tool_args['query']
                                filepath = tool_args['filepath']
                                file_structure = tool_args['file_structure']
                                generated_code = code_generator_tool(query, filepath, file_structure)
                                print(f"Generated code: {generated_code}")

                                # 调用 code_executor_tool 执行生成的代码
                                result = code_executor_tool(generated_code)
                                print(f"Execution result: {result}")

                                # 构建新的消息，将执行结果传递给大模型
                                new_user_prompt = f"代码执行结果为: {result}。请根据这个结果总结输出。"
                                new_messages = messages + [{"role": "assistant", "content": content}, {"role": "user", "content": new_user_prompt}]
                                new_data = {
                                    "model": "qwen2.5:latest",
                                    "messages": new_messages,
                                    "temperature": 0.3
                                }
                                new_response = requests.post(f"{base_url}/v1/chat/completions", json=new_data)
                                new_response_json = new_response.json()
                                summary = new_response_json['choices'][0]['message'].get('content', '')
                                logger.info(f"总结输出: {summary}")
                                st.markdown(summary)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse tool_call_str as JSON: {tool_call_str}, error: {e}")
                    else:
                        logger.warning("Tool call tags found, but indices are invalid.")
                else: 
                    logger.info(f"answer directly: {content}")
                    st.markdown(content)
            elif finish_reason == "tool_calls":
                for tool_call in response_json['choices'][0]['message']['tool_calls']:                        
                    tool_name = tool_call['function']['name']
                    tool_args = tool_call['function']['arguments']
                    try: 
                        tool_args = json.loads(tool_args)
                        print(f"tool_args: {tool_args}")
                        if tool_name == "code_generator_tool":
                            query = tool_args['query']
                            filepath = tool_args['filepath']
                            file_structure = tool_args['file_structure']
                            generated_code = code_generator_tool(query, filepath, file_structure)
                            print(f"Generated code: {generated_code}")

                            # 调用 code_executor_tool 执行生成的代码
                            result = code_executor_tool(generated_code)
                            print(f"Execution result: {result}")

                            # 构建新的消息，将执行结果传递给大模型
                            new_user_prompt = f"代码执行结果为: {result}。请根据这个结果总结输出。"
                            new_messages = messages + [{"role": "assistant", "content": response_json['choices'][0]['message']['content']}, {"role": "user", "content": new_user_prompt}]
                            new_data = {
                                "model": "qwen2.5:latest",
                                "messages": new_messages,
                                "temperature": 0.3
                            }
                            new_response = requests.post(f"{base_url}/v1/chat/completions", json=new_data)
                            new_response_json = new_response.json()
                            summary = new_response_json['choices'][0]['message'].get('content', '')
                            print(f"总结输出: {summary}")
                            st.markdown(summary)


                    except json.JSONDecodeError:
                        print("解析 tool_call 的 JSON 数据时出错，请检查格式。")
