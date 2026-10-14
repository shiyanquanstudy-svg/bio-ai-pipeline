import streamlit as st
import json
from pathlib import Path
from db_helper import init_db
from pipeline import run_pipeline
import requests  # 新增

# 1. 页面基础设置
st.set_page_config(
    page_title="Bio-AI 自动化平台",
    page_icon="🧬",
    layout="centered"
)

# ==================== 新增：侧边栏调试区 ====================
st.sidebar.header("🛠️ 调试面板")

# 第二步：显示云端/本地读取到的 Key
try:
    key_preview = st.secrets.get("DEEPSEEK_API_KEY", "未找到")
except:
    key_preview = "未找到"

st.sidebar.write("**当前读取到的 Key：**")
if key_preview != "未找到":
    # 只显示前6位和后4位，保证安全
    masked_key = key_preview[:6] + "****" + key_preview[-4:]
    st.sidebar.success(f"{masked_key}")
else:
    st.sidebar.error("未找到 Key！")

# 第三步：网络连通性测试按钮
if st.sidebar.button("🌐 测试 DeepSeek 网络"):
    try:
        res = requests.get("https://api.deepseek.com", timeout=5)
        st.sidebar.success(f"网络正常，状态码：{res.status_code}")
    except Exception as e:
        st.sidebar.error(f"网络不通：{e}")

# 临时显示完整 Secrets 结构（部署稳定后可以删除）
if st.sidebar.checkbox("显示所有 Secrets 键名"):
    try:
        st.sidebar.write(list(st.secrets.keys()))
    except:
        st.sidebar.write("无法读取 Secrets")
# ==========================================================

# 2. 初始化数据库
init_db()

# 3. 页面标题与说明
st.title("🧬 Bio-AI 蛋白质分析自动化平台")
st.markdown("""
输入一个 **UniProt ID**，系统将自动完成：
1. 从 UniProt 抓取蛋白质数据
2. 调用 AI 进行功能与定位分析
3. 将结果存入本地数据库（重复分析零成本）
""")

# 4. 输入区
uniprot_id = st.text_input(
    "请输入 UniProt ID（例如 P04637）：",
    value="P04637",
    help="人类 P53 蛋白的 UniProt ID 是 P04637"
)

# 5. 执行按钮
if st.button("🚀 开始分析", type="primary"):
    if not uniprot_id.strip():
        st.warning("⚠️ 请输入有效的 UniProt ID！")
    else:
        uid = uniprot_id.strip()
        
        # 显示加载动画
        with st.spinner(f"正在处理 {uid}，请稍候..."):
            try:
                success = run_pipeline(uid)
            except Exception as e:
                import traceback
                st.error(f"💥 发生异常：{e}")
                st.code(traceback.format_exc())
                success = False
        
        if success:
            st.success(f"✅ {uid} 分析完成！")
            
            # 尝试读取并展示结果
            ai_json_path = Path(f"data/ai_analysis_{uid}.json")
            if ai_json_path.exists():
                with open(ai_json_path, "r", encoding="utf-8") as f:
                    ai_data = json.load(f)
                
                st.markdown("### 📊 AI 分析结果")
                st.json(ai_data)
                st.info("💡 如果结果来自本地缓存，则本次没有消耗任何 AI 额度。")
            else:
                st.warning("⚠️ 结果文件未找到，请查看终端日志。")
        else:
            st.error(f"❌ {uid} 分析失败，请检查 ID 是否正确，或查看终端报错信息。")

# 6. 页脚
st.markdown("---")
st.caption("Bio-AI 自动化平台 · 基于 Python + Streamlit + UniProt + LLM")