import os, re, requests

def extract_python_code(content):
    code_pattern = r"```python\n(.*?)\n```"
    match = re.search(code_pattern, content, re.DOTALL)
    if match:
        code = match.group(1)
        print(f"extracted python code: \n{code}")
        return code
    else:
        return None

def code_generator_tool(query, filepath, file_structure, model="qwen2.5:latest"):   
    base_url = os.getenv("LLM_HOST")

    # 系统提示词
    sys_prompt = """
    你是一个专业的数据分析助手，请根据用户提供的 Excel 文件以及文件结构，针对用户问题生成 Python 代码来处理文件。

    请按如下格式返回 Python 代码：
    ```python
    # 这里是 Python 代码
    ```
    """
    # 用户信息
    user_prompt = f"""
    Excel文件: {filepath}
    Excel结构信息: {file_structure}
    用户问题: {query}
    """

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ]
    data = {
        "model": model,
        "messages": messages
    }
    response = requests.post(f"{base_url}/v1/chat/completions", json=data).json()
    if response.get("error"):
        print(f"CodeGenerationTool - LLM 解析错误: {response['error']['message']}")
        return None
    elif response.get("choices"):
        content = response["choices"][0]["message"]["content"]
        print(f"CodeGenerationTool - LLM 解析结果: {content}")
        python_code = extract_python_code(content)
        return python_code
    else:
        return None