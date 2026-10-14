import json
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def summarize(data):
    results = []
    for sample in data["samples"]:
        yield_per_a280 = sample["yield_mg"] / sample["a280"]
        a280_per_yield = sample["a280"] / sample["yield_mg"]
        results.append({
            "id": sample["id"],
            "yield_mg": sample["yield_mg"],
            "a280": sample["a280"],
            "yield_per_a280": round(yield_per_a280, 2),
            "a280_per_yield": round(a280_per_yield, 3),
            "flag": "high" if sample["yield_mg"] > 5 else "normal"
        })
    return results


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    data = load_json("data/sample.json")
    results = summarize(data)

    output = {
        "experiment": data["experiment"],
        "date": data["date"],
        "results": results
    }

    save_json("data/result_2026-10-14.json", output)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()