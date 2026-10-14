import os
import json
import requests
from pathlib import Path    # <--- 加上这一行！
import streamlit as st
from dotenv import load_dotenv

# 1. 先尝试从本地 .env 加载
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

# 2. 如果本地没有（云端环境），从 Streamlit Secrets 读取
if not api_key:
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = None

# 3. 如果都没有，报错退出
if not api_key:
    print("错误：未找到 DEEPSEEK_API_KEY，请检查 .env 文件或 Streamlit Secrets！")
    exit()


def analyze_protein(input_file, output_file):
    """
    读取蛋白质数据，调用 AI 分析，并保存结构化结果。
    :param input_file: 输入 JSON 文件路径（如 data/protein_P04637.json）
    :param output_file: 输出 JSON 文件路径（如 data/ai_analysis_P04637.json）
    :return: AI 分析后的字典，失败返回 None
    """
    # 1. 校验密钥
    if not api_key:
        print("错误：未找到 DEEPSEEK_API_KEY，请检查 .env 文件！")
        return None

    # 2. 读取上游数据
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"错误：找不到 {input_path}")
        return None

    with open(input_path, "r", encoding="utf-8") as f:
        protein_data = json.load(f)

    # 3. 构造请求头
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 4. 构造提示词
    system_prompt = """你是一个专业的生物化学分析助手。
你的任务是根据输入的蛋白质信息，提取并总结关键信息。
你必须严格输出 JSON 格式，不要包含任何其他文字（如 ```json 标记）。
JSON 必须包含以下字段：
- gene_name: 基因名
- function_summary: 蛋白质功能的一句话总结（中文）
- subcellular_location: 亚细胞定位（中文）
- family: 蛋白质家族（如果无法确定填 "Unknown"）
"""

    user_prompt = f"""请分析以下蛋白质数据：
UniProt ID: {protein_data.get('uniprot_id', 'N/A')}
蛋白名称: {protein_data.get('protein_name', 'N/A')}
物种: {protein_data.get('organism', 'N/A')}
序列长度: {protein_data.get('length', 0)}
序列: {protein_data.get('sequence', '')[:200]}... (此处仅截取前200个氨基酸)
"""

    # 5. 构造请求体
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }

    # 6. 发送 POST 请求
    print(f"正在请求 AI 分析 {input_file} ...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        print(f"请求失败，状态码：{response.status_code}")
        print(response.text)
        return None

    # 7. 解析与清洗
    result = response.json()
    ai_content = result["choices"][0]["message"]["content"].strip()

    if ai_content.startswith("```json"):
        ai_content = ai_content[7:]
    if ai_content.endswith("```"):
        ai_content = ai_content[:-3]
    ai_content = ai_content.strip()

    try:
        ai_data = json.loads(ai_content)
    except json.JSONDecodeError:
        print("错误：AI 返回的不是合法的 JSON！")
        print("原始返回：", ai_content)
        return None

    # 8. 保存结果
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ai_data, f, ensure_ascii=False, indent=2)

    print(f"AI 分析完成！已保存到 {output_path}")
    return ai_data


if __name__ == "__main__":
    # 测试两个不同的蛋白
    result1 = analyze_protein("data/protein_P04637.json", "data/ai_analysis_P04637.json")
    if result1:
        print(json.dumps(result1, ensure_ascii=False, indent=2))

    print("-" * 50)
    
    result2 = analyze_protein("data/protein_P06213.json", "data/ai_analysis_P06213.json")
    if result2:
        print(json.dumps(result2, ensure_ascii=False, indent=2))