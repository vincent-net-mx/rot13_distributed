import codecs
import os
from flask import Flask, jsonify, request

app = Flask(__name__)
WORKER_ID = os.getenv("WORKER_ID", "unknown")


def apply_rot13(text: str) -> str:
    # codecs maneja caracteres ASCII respetando mayúsculas y minúsculas
    return codecs.encode(text, "rot_13")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "worker_id": WORKER_ID}), 200


@app.route("/process", methods=["POST"])
def process():
    data = request.get_json(force=True)
    chunk = data.get("chunk", "")

    transformed = apply_rot13(chunk)

    return (
        jsonify(
            {
                "worker_id": WORKER_ID,
                "input_chunk": chunk,
                "output_chunk": transformed,
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
