import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fetch_uniprot import fetch_protein
from ask_ai import analyze_protein
from pathlib import Path
from db_helper import init_db,get_cached_result,get_cached_result_with_time,save_result,get_all_ids



def run_pipeline(uniprot_id):
    """
    一键流水线：抓取数据 -> AI分析 -> 保存报告
    """
    print(f"\n{'='*50}")
    print(f"开始处理 UniProt ID: {uniprot_id}")
    print(f"{'='*50}")

    # === 缓存检查（带时间） ===
    cached_data, cached_time = get_cached_result_with_time(uniprot_id)
    if cached_data:
        print(f"⚡ 发现缓存！跳过 UniProt 抓取和 AI 调用。")
        print(f"缓存时间：{cached_time}")
        print(f"缓存的结果摘要：{cached_data.get('function_summary', 'N/A')}")
        return True
    # ==========================

    # 定义流水线中的文件路径
    raw_json = f"data/protein_{uniprot_id}.json"
    ai_json = f"data/ai_analysis_{uniprot_id}.json"

    # === 新增：统一的失败记录工具函数 ===
    def log_failure(reason):
        """把失败的 ID 记录到 data/failed_ids.txt"""
        log_path = Path("data/failed_ids.txt")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{uniprot_id}\t{reason}\t{raw_json}\n")
        print(f"📝 已将失败记录写入 {log_path}")

    try:
        # 第一步：抓取 UniProt 数据
        print(f"[步骤 1/2] 正在抓取 {uniprot_id} 的蛋白质数据...")
        protein_data = fetch_protein(uniprot_id)
        
        if not protein_data:
            print(f"❌ 抓取失败，跳过 {uniprot_id}")
            log_failure("fetch_failed")  # 记录抓取失败
            return False

        # 第二步：调用 AI 分析
        print(f"[步骤 2/2] 正在调用 AI 分析 {uniprot_id}...")
        ai_result = analyze_protein(raw_json, ai_json)

        if not ai_result:
            print(f"❌ AI 分析失败，跳过 {uniprot_id}")
            log_failure("ai_failed")  # 记录 AI 失败
            return False

        # ======================== 新增这一行 ========================
        save_result(uniprot_id, ai_result)
        print(f"💾 已将分析结果写入数据库")
        # ===========================================================

        print(f"✅ {uniprot_id} 流水线处理完成！报告已保存至 {ai_json}")
        return True

    except Exception as e:
        # 终极容错：任何意外报错都不会让整个程序崩溃
        print(f"❌ 处理 {uniprot_id} 时发生异常：{e}")
        log_failure(f"exception: {e}")  # 记录异常
        return False
    
if __name__ == "__main__":
    # 批量处理一个 ID 列表
    init_db()
    target_ids = ["P04637", "P06213", "P00533", "P12345", "P69905", "P01308"]
    
    MAX_WORKERS = 3
    print(f"\n{'='*50}")
    print(f"启动并发流水线，共 {len(target_ids)} 个任务，并发数：{MAX_WORKERS}")
    print(f"{'='*50}")

    success_count = 0
    start_time = time.time()  # 记录开始时间

    # 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_uid = {
            executor.submit(run_pipeline, uid): uid for uid in target_ids
        }

        # 谁先做完，谁就先返回结果（as_completed）
        for future in as_completed(future_to_uid):
            uid = future_to_uid[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
            except Exception as e:
                print(f"❌ {uid} 并发执行时发生异常：{e}")

    elapsed = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"流水线执行完毕！成功 {success_count} / {len(target_ids)} 个任务，耗时 {elapsed:.2f} 秒。")
    print(f"{'='*50}")