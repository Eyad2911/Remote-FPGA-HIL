import base64
import json
import struct

_HEADER_FMT = ">I"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)
_MAX_PAYLOAD = 16 * 1024 * 1024  # 16 MB cap (bitstreams can be large)


class ProtocolError(Exception):
    pass


# ── Packet builders ────────────────────────────────────────────────────────────

def ping_packet() -> dict:
    return {"header": "PING"}


def alsu_packet(op: str, a: int, b: int) -> dict:
    return {"header": "ALSU", "op": op, "a": a, "b": b}


def file_packet(filename: str, data: bytes) -> dict:
    return {
        "header": "FILE",
        "filename": filename,
        "size": len(data),
        "payload": base64.b64encode(data).decode("ascii"),
    }


# ── Wire encoding / decoding ───────────────────────────────────────────────────

def encode_message(msg: dict) -> bytes:
    payload = json.dumps(msg, separators=(",", ":")).encode("utf-8")
    header = struct.pack(_HEADER_FMT, len(payload))
    return header + payload


def recv_message(sock) -> dict:
    raw_header = _recv_exact(sock, _HEADER_SIZE)
    if len(raw_header) < _HEADER_SIZE:
        raise ProtocolError("Connection closed before header was received.")
    (payload_length,) = struct.unpack(_HEADER_FMT, raw_header)
    if payload_length > _MAX_PAYLOAD:
        raise ProtocolError(
            f"Declared payload length {payload_length} exceeds limit {_MAX_PAYLOAD}."
        )
    raw_payload = _recv_exact(sock, payload_length)
    if len(raw_payload) < payload_length:
        raise ProtocolError(
            f"Connection closed after {len(raw_payload)} of {payload_length} bytes."
        )
    return json.loads(raw_payload.decode("utf-8"))


def _recv_exact(sock, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)
