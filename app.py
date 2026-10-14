import streamlit as st
import json
from pathlib import Path
from db_helper import init_db
from pipeline import run_pipeline

# 1. 页面基础设置
st.set_page_config(
    page_title="Bio-AI 自动化平台",
    page_icon="🧬",
    layout="centered"
)

# 2. 初始化数据库（每次刷新页面都会确保数据库存在）
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
            success = run_pipeline(uid)
        
        if success:
            st.success(f"✅ {uid} 分析完成！")
            
            # 尝试读取并展示结果
            ai_json_path = Path(f"data/ai_analysis_{uid}.json")
            if ai_json_path.exists():
                with open(ai_json_path, "r", encoding="utf-8") as f:
                    ai_data = json.load(f)
                
                st.markdown("### 📊 AI 分析结果")
                st.json(ai_data)
                
                # 如果是缓存命中，再补一句提示
                st.info("💡 如果结果来自本地缓存，则本次没有消耗任何 AI 额度。")
            else:
                st.warning("⚠️ 结果文件未找到，请查看终端日志。")
        else:
            st.error(f"❌ {uid} 分析失败，请检查 ID 是否正确，或查看终端报错信息。")

# 6. 页脚
st.markdown("---")
st.caption("Bio-AI 自动化平台 · 基于 Python + Streamlit + UniProt + LLM")