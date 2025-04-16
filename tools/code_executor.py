import sys
from io import StringIO

def code_executor_tool(code):
    try:
        # 创建一个 StringIO 对象来捕获 print 输出
        old_stdout = sys.stdout
        new_stdout = StringIO()
        sys.stdout = new_stdout

        loc = locals()
        exec(code, globals(), loc)

        # 获取捕获的 print 输出
        output = new_stdout.getvalue()

        # 恢复标准输出
        sys.stdout = old_stdout

        # 尝试获取 result 变量的值
        result = loc.get("result")

        # 如果有 result 变量的值，优先返回它，否则返回 print 输出
        if result is not None:
            return result
        else:
            return output
    except Exception as e:
        print(f"CodeExecutorTool - 代码执行错误: {e}")
        return None