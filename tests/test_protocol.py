import json
import socket
import struct

import pytest

from pc_gui.networking.protocol import (
    ProtocolError,
    _HEADER_FMT,
    _HEADER_SIZE,
    alsu_packet,
    encode_message,
    file_packet,
    ping_packet,
    recv_message,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_socket_pair():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", port))
    conn, _ = server.accept()
    server.close()
    return client, conn


def _roundtrip(msg):
    sender, receiver = _make_socket_pair()
    try:
        sender.sendall(encode_message(msg))
        sender.close()
        return recv_message(receiver)
    finally:
        receiver.close()


# ── Packet builder tests ───────────────────────────────────────────────────────

class TestPacketBuilders:
    def test_ping_packet_shape(self):
        p = ping_packet()
        assert p == {"header": "PING"}

    def test_alsu_packet_shape(self):
        p = alsu_packet("ADD", 10, 5)
        assert p == {"header": "ALSU", "op": "ADD", "a": 10, "b": 5}

    def test_alsu_packet_all_ops(self):
        for op in ("ADD", "SUB", "MUL", "SHIFT", "BYPASS", "XOR"):
            p = alsu_packet(op, 1, 2)
            assert p["header"] == "ALSU"
            assert p["op"] == op

    def test_file_packet_shape(self):
        data = b"fake bitstream bytes"
        p = file_packet("design.bit", data)
        assert p["header"] == "FILE"
        assert p["filename"] == "design.bit"
        assert p["size"] == len(data)
        assert "payload" in p

    def test_file_packet_payload_is_base64(self):
        import base64
        data = b"\x00\x01\x02\x03\xFF\xFE"
        p = file_packet("test.bit", data)
        decoded = base64.b64decode(p["payload"])
        assert decoded == data

    def test_file_packet_empty_file(self):
        p = file_packet("empty.bit", b"")
        assert p["size"] == 0


# ── encode_message tests ───────────────────────────────────────────────────────

class TestEncodeMessage:
    def test_returns_bytes(self):
        assert isinstance(encode_message(ping_packet()), bytes)

    def test_header_length_field_correct(self):
        msg = alsu_packet("ADD", 10, 5)
        encoded = encode_message(msg)
        (declared,) = struct.unpack(_HEADER_FMT, encoded[:_HEADER_SIZE])
        assert declared == len(encoded[_HEADER_SIZE:])

    def test_payload_is_valid_json(self):
        msg = alsu_packet("XOR", 7, 3)
        encoded = encode_message(msg)
        (plen,) = struct.unpack(_HEADER_FMT, encoded[:_HEADER_SIZE])
        assert json.loads(encoded[_HEADER_SIZE:_HEADER_SIZE + plen]) == msg

    def test_empty_dict(self):
        encoded = encode_message({})
        (plen,) = struct.unpack(_HEADER_FMT, encoded[:_HEADER_SIZE])
        assert plen >= 2

    def test_nested_dict(self):
        msg = {"header": "META", "data": {"nested": [1, 2, 3]}}
        encoded = encode_message(msg)
        (plen,) = struct.unpack(_HEADER_FMT, encoded[:_HEADER_SIZE])
        assert json.loads(encoded[_HEADER_SIZE:_HEADER_SIZE + plen]) == msg


# ── recv_message round-trip tests ─────────────────────────────────────────────

class TestRecvMessage:
    def test_ping_roundtrip(self):
        assert _roundtrip(ping_packet()) == ping_packet()

    def test_alsu_request_roundtrip(self):
        msg = alsu_packet("ADD", 10, 5)
        assert _roundtrip(msg) == msg

    def test_alsu_response_roundtrip(self):
        msg = {"status": "ok", "result": 15}
        assert _roundtrip(msg) == msg

    def test_file_packet_roundtrip(self):
        data = b"fake bitstream" * 100
        p = file_packet("design.bit", data)
        result = _roundtrip(p)
        assert result["header"] == "FILE"
        assert result["filename"] == "design.bit"
        assert result["size"] == len(data)

    def test_error_response_roundtrip(self):
        msg = {"status": "error", "message": "Unknown header"}
        assert _roundtrip(msg) == msg

    def test_multiple_sequential_messages(self):
        sender, receiver = _make_socket_pair()
        try:
            m1 = ping_packet()
            m2 = alsu_packet("SUB", 10, 3)
            sender.sendall(encode_message(m1) + encode_message(m2))
            sender.close()
            assert recv_message(receiver) == m1
            assert recv_message(receiver) == m2
        finally:
            receiver.close()

    def test_raises_on_closed_connection(self):
        sender, receiver = _make_socket_pair()
        sender.close()
        with pytest.raises(ProtocolError, match="header"):
            recv_message(receiver)
        receiver.close()

    def test_raises_on_truncated_payload(self):
        sender, receiver = _make_socket_pair()
        try:
            sender.sendall(struct.pack(_HEADER_FMT, 100) + b"x" * 10)
            sender.close()
            with pytest.raises(ProtocolError, match="closed after"):
                recv_message(receiver)
        finally:
            receiver.close()

    def test_raises_on_oversized_payload(self):
        sender, receiver = _make_socket_pair()
        try:
            sender.sendall(struct.pack(_HEADER_FMT, 20 * 1024 * 1024))
            sender.close()
            with pytest.raises(ProtocolError, match="exceeds limit"):
                recv_message(receiver)
        finally:
            receiver.close()
