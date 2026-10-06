import math
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify, render_template, request
import requests

app = Flask(__name__)

WORKERS = [
    {"id": 1, "url": "http://worker-1:5000/process"},
    {"id": 2, "url": "http://worker-2:5000/process"},
    {"id": 3, "url": "http://worker-3:5000/process"},
]


def split_string_into_three(text: str) -> list[str]:
    n = len(text)
    if n == 0:
        return ["", "", ""]

    base = n // 3
    remainder = n % 3

    # Distribuye el residuo entre los primeros nodos
    s1_len = base + (1 if remainder > 0 else 0)
    s2_len = base + (1 if remainder > 1 else 0)

    part1 = text[:s1_len]
    part2 = text[s1_len : s1_len + s2_len]
    part3 = text[s1_len + s2_len :]

    return [part1, part2, part3]


def send_to_worker(worker_info: dict, chunk: str) -> dict:
    try:
        response = requests.post(
            worker_info["url"], json={"chunk": chunk}, timeout=5
        )
        if response.status_code == 200:
            payload = response.json()
            return {
                "worker_id": worker_info["id"],
                "status": "success",
                "input": chunk,
                "output": payload.get("output_chunk", ""),
            }
        return {
            "worker_id": worker_info["id"],
            "status": "error",
            "input": chunk,
            "output": "",
            "error": f"HTTP {response.status_code}",
        }
    except Exception as e:
        return {
            "worker_id": worker_info["id"],
            "status": "error",
            "input": chunk,
            "output": "",
            "error": str(e),
        }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process_pipeline():
    data = request.get_json(force=True)
    raw_text = data.get("text", "")

    chunks = split_string_into_three(raw_text)

    # Procesamiento concurrente hacia los 3 nodos
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(send_to_worker, worker, chunk)
            for worker, chunk in zip(WORKERS, chunks)
        ]
        results = [f.result() for f in futures]

    # Reensamblado preservando el orden original
    results.sort(key=lambda r: r["worker_id"])
    final_text = "".join(r["output"] for r in results)

    return (
        jsonify(
            {
                "original_text": raw_text,
                "chunks": chunks,
                "workers_data": results,
                "assembled_result": final_text,
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
