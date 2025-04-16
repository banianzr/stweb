import logging, os

from datetime import datetime

def get_logger(page_name: str) -> logging.Logger:
    # 确保日志目录存在
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 使用当前时间生成日志文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    log_filename = os.path.join(log_dir, f"{page_name}-{timestamp}.log")
    
    # 创建logger对象
    logger = logging.getLogger(page_name)
    logger.setLevel(logging.INFO)
    
    # 防止重复添加handler
    if logger.hasHandlers():
        logger.handlers.clear()

    # 定义日志格式
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # 文件Handler：写入日志文件
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # 控制台Handler：输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 将两个handler添加到logger中
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
