import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fetch_uniprot import fetch_protein
from ask_ai import analyze_protein
from pathlib import Path
from db_helper import init_db,get_cached_result,get_cached_result_with_time,save_result,get_all_ids



def run_pipeline(uniprot_id):
    print(f"\n{'='*50}")
    print(f"开始处理 UniProt ID: {uniprot_id}")
    print(f"{'='*50}")

    cached_data, cached_time = get_cached_result_with_time(uniprot_id)
    if cached_data:
        print(f"⚡ 发现缓存！跳过 UniProt 抓取和 AI 调用。")
        return True

    raw_json = f"data/protein_{uniprot_id}.json"
    ai_json = f"data/ai_analysis_{uniprot_id}.json"

    def log_failure(reason):
        log_path = Path("data/failed_ids.txt")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{uniprot_id}\t{reason}\t{raw_json}\n")
        print(f"📝 已将失败记录写入 {log_path}")

    try:
        print(f"[步骤 1/2] 正在抓取 {uniprot_id} 的蛋白质数据...")
        protein_data = fetch_protein(uniprot_id)
        
        if not protein_data:
            log_failure("fetch_failed")
            # === 关键修改 1：抛出异常而不是返回 False ===
            raise Exception(f"抓取 {uniprot_id} 失败，可能是 UniProt 网络不通或 ID 错误")

        print(f"[步骤 2/2] 正在调用 AI 分析 {uniprot_id}...")
        ai_result = analyze_protein(raw_json, ai_json)

        if not ai_result:
            log_failure("ai_failed")
            # === 关键修改 2：抛出异常而不是返回 False ===
            raise Exception(f"AI 分析 {uniprot_id} 失败，可能是 DeepSeek 网络不通或 API Key 错误")

        save_result(uniprot_id, ai_result)
        print(f"✅ {uniprot_id} 流水线处理完成！报告已保存至 {ai_json}")
        return True

    except Exception as e:
        print(f"❌ 处理 {uniprot_id} 时发生异常：{e}")
        log_failure(f"exception: {e}")
        # === 关键修改 3：重新抛出异常，让上层捕获 ===
        raise e
    
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