"""
Root Club Special Login - Flask Backend
========================================

Issues encrypted credential tokens. Holders submit tokens to /api/submit
to verify their access tier.

Token format
------------
Plaintext: "name=USERNAME;tier=TIER;ref=REFCODE"
Wire format: base64( IV || AES_CBC_PKCS7(plaintext) )
"""

import base64
import os
import secrets
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


app = Flask(__name__)

CORS(
    app,
    origins=[
        "https://<enter-Domain>",
    ],
)



_key_hex = os.environ.get("AES_KEY")
if _key_hex:
    AES_KEY = bytes.fromhex(_key_hex)
else:
    AES_KEY = secrets.token_bytes(16)
    print(f"Generated AES_KEY: {AES_KEY.hex()} -- set this as env var to persist across restarts")

BLOCK_SIZE = 16
NAME_FORBIDDEN = (";", "=", "\n", "\r", "\x00")
FLAG = "FLAG{}"


class InvalidPadding(Exception):
    """Raised specifically when PKCS7 unpadding fails. Distinct from any
    other ValueError that could come out of the decrypt path (length guard,
    base64 decode, AES block-size mismatch) so the route handler can return
    a different status for padding-only failures."""
    pass


def encrypt_token(plaintext: str) -> str:
    pt_bytes = plaintext.encode("utf-8")
    padder = padding.PKCS7(BLOCK_SIZE * 8).padder()
    padded = padder.update(pt_bytes) + padder.finalize()
    iv = secrets.token_bytes(BLOCK_SIZE)
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode("ascii")


def decrypt_token(token_b64: str) -> str:
    raw = base64.b64decode(token_b64)
    if len(raw) < 2 * BLOCK_SIZE or (len(raw) - BLOCK_SIZE) % BLOCK_SIZE != 0:
        raise ValueError("bad length")
    iv = raw[:BLOCK_SIZE]
    ciphertext = raw[BLOCK_SIZE:]
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(BLOCK_SIZE * 8).unpadder()
    try:
        plaintext_bytes = unpadder.update(padded_plaintext) + unpadder.finalize()
    except ValueError as e:
        raise InvalidPadding(str(e)) from e

    return plaintext_bytes.decode("utf-8", errors="replace")


def parse_token_plaintext(plaintext: str) -> dict:
    # Lenient: silently skip chunks without '=' instead of raising. After a
    # padding-valid decrypt the plaintext can contain U+FFFD replacement
    # chars (decode errors='replace'), so partial structure is expected.
    result = {}
    for chunk in plaintext.split(";"):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def build_token(name: str, tier: str, ref: str) -> str:
    return encrypt_token(f"name={name};tier={tier};ref={ref}")


@app.route("/api/issue", methods=["POST"])
def issue():
    """Issue a basic-tier credential token for the supplied name."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name or len(name) > 64 or any(c in name for c in NAME_FORBIDDEN):
        return jsonify({"error": "invalid name"}), 400

    ref = f"{secrets.randbelow(10000):04d}"
    token = build_token(name, "basic", ref)
    return jsonify({"token": token}), 200


# WARNING: 60/min throttles legitimate attack traffic. The padding oracle
# attack needs thousands of /api/submit calls in a short window to recover
# plaintext byte-by-byte (~256 tries per byte). Raise this limit (or
# disable it) before exposing the lab to students -- otherwise the
# challenge is effectively unsolvable. On a shared classroom NAT, divide
# the budget by the number of students sharing the IP, which makes it
# even tighter.
@app.route("/api/submit", methods=["POST"])
def submit():
    """Verify a submitted credential token."""
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    if not token:
        return jsonify({"message": "Access Denied"}), 200

    try:
        plaintext = decrypt_token(token)
    except InvalidPadding:
        return "", 400
    except Exception:
        return jsonify({"message": "Access Denied"}), 200

    # Parse is lenient (never raises); padding was valid above so we always
    # reach this -- the only gate to the flag is tier == "elite".
    fields = parse_token_plaintext(plaintext)
    name = fields.get("name", "operator")
    tier = fields.get("tier", "")

    if tier == "elite":
        return jsonify({
            "message": "Welcome, elite member. Access granted.",
            "flag": FLAG,
        }), 200

    return jsonify({"message": f"Welcome, {name}."}), 200


@app.route("/source", methods=["GET"])
def source():
    body = (
        "# root club -- backend transport (internal)\n"
        "#\n"
        "# token: base64( iv || ciphertext )\n"
        "# 16-byte blocks; blocks chain on decode -- a flip in one block shifts the next.\n"
        "# integrity check: implicit. key rotates per process restart.\n"
        "#\n"
        "# pre-launch checklist:\n"
        "#   [x] CORS pinned to dev origins\n"
        "#   [ ] rate-limit /api/submit\n"
        "#   [ ] audit 4xx response shape on /api/submit before public release\n"
    )
    return Response(body, status=200, mimetype="text/plain")


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port, debug=False)
