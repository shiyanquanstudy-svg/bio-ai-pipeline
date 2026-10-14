import requests
import json
from pathlib import Path
import csv

def fetch_protein(uniprot_id):
    # 1. 定义 API 地址（动态拼接 ID）
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    
    # 2. 发送请求
    print(f"正在请求 {uniprot_id} ...")
    response = requests.get(url, timeout=10)
    
    if response.status_code != 200:
        print(f"请求失败，状态码：{response.status_code}")
        return None  # 函数里出错要返回 None，而不是 exit()
    
    data = response.json()
    
    # 3. 提取数据（加入容错 .get()）
    # 基因名（安全写法）
    gene_name = data.get("genes", [{}])[0].get("geneName", {}).get("value", "N/A")
    
    # 蛋白名（如果推荐名没有，可以尝试找替代名）
    protein_name = data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "N/A")
    
    organism = data.get("organism", {}).get("scientificName", "N/A")
    sequence = data.get("sequence", {}).get("value", "")
    length = data.get("sequence", {}).get("length", 0)
    
    # 4. 组装
    protein_info = {
        "gene_name": gene_name,
        "uniprot_id": uniprot_id,
        "protein_name": protein_name,
        "organism": organism,
        "length": length,
        "sequence": sequence
    }
    
    # 5. 动态生成文件名并保存 JSON
    json_path = Path(f"data/protein_{uniprot_id}.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(protein_info, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {json_path}")
    
    # 6. 动态生成文件名并保存 CSV
    csv_path = Path(f"data/protein_{uniprot_id}.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=protein_info.keys())
        writer.writeheader()
        writer.writerow(protein_info)
    print(f"已保存到 {csv_path}")
    
    return protein_info

if __name__ == "__main__":
    # 调用函数，抓取两个不同的蛋白
    fetch_protein("P04637")  # P53
    fetch_protein("P06213")  # 胰岛素受体