import argparse
import base64
import logging
import os
import socket
import tempfile
import threading

from pi_server.bitstream_programmer import BitstreamError, BitstreamProgrammer
from pi_server.fpga_bridge import FPGABridge, FPGABridgeError
from pi_server.protocol import ProtocolError, encode_message, recv_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Client handler ─────────────────────────────────────────────────────────────

def _handle_client(conn, addr, bridge):
    peer = f"{addr[0]}:{addr[1]}"
    log.info("Client connected: %s", peer)
    try:
        while True:
            try:
                msg = recv_message(conn)
            except ProtocolError as exc:
                log.warning("Protocol error from %s: %s", peer, exc)
                try:
                    conn.sendall(encode_message({"status": "error", "message": f"Protocol error: {exc}"}))
                except OSError:
                    pass
                break
            except Exception as exc:
                log.debug("recv ended for %s: %s", peer, exc)
                break

            header = msg.get("header", "")
            log.info("<- %s  header=%r", peer, header)

            try:
                response = _dispatch(header, msg, bridge)
            except Exception as exc:
                log.error("Unhandled error dispatching %r from %s: %s", header, peer, exc, exc_info=True)
                response = {"status": "error", "message": f"Internal server error: {exc}"}

            log.info("-> %s  status=%r", peer, response.get("status"))

            try:
                conn.sendall(encode_message(response))
            except OSError as exc:
                log.warning("Send to %s failed: %s", peer, exc)
                break
    finally:
        conn.close()
        log.info("Client disconnected: %s", peer)


# ── Dispatcher ─────────────────────────────────────────────────────────────────

def _dispatch(header, msg, bridge):
    if header == "PING":
        return {"status": "ok", "message": "pong"}
    if header == "ALSU":
        if bridge is None:
            return {"status": "error", "message": "FPGA ALSU bridge unavailable (UART init failed — check --uart-port)."}
        return _handle_alsu(msg, bridge)
    if header == "FILE":
        return _handle_file(msg)
    return {"status": "error", "message": f"Unknown header: {header!r}"}


def _handle_alsu(msg, bridge):
    op = msg.get("op", "")
    try:
        a = int(msg["a"])
        b = int(msg.get("b", 0))
    except (KeyError, TypeError, ValueError) as exc:
        return {"status": "error", "message": f"Bad operands: {exc}"}
    try:
        result = bridge.compute(op, a, b)
        return {"status": "ok", "result": result}
    except FPGABridgeError as exc:
        return {"status": "error", "message": str(exc)}


def _handle_file(msg):
    filename = msg.get("filename", "upload.bit")
    b64_payload = msg.get("payload", "")
    declared_size = msg.get("size", 0)

    try:
        data = base64.b64decode(b64_payload)
    except Exception as exc:
        return {"status": "error", "message": f"base64 decode failed: {exc}"}

    if len(data) != declared_size:
        log.warning(
            "File size mismatch: declared %d, received %d bytes", declared_size, len(data)
        )

    log.info("Received %d bytes for %s", len(data), filename)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".bit", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        programmer = BitstreamProgrammer()
        programmer.program(tmp_path)
        log.info("FPGA programmed successfully with %s", filename)
        return {"status": "ok", "message": f"FPGA programmed with {filename}"}

    except BitstreamError as exc:
        return {"status": "error", "message": str(exc)}
    except Exception as exc:
        return {"status": "error", "message": f"Unexpected error: {exc}"}
    finally:
        if tmp_path and os.path.isfile(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ── Server entry point ─────────────────────────────────────────────────────────

def run_server(host="0.0.0.0", port=5000, uart_port="/dev/ttyUSB0", baud=115200):
    try:
        bridge = FPGABridge(port=uart_port, baud=baud)
        log.info("FPGA bridge opened on %s at %d baud.", uart_port, baud)
    except Exception as exc:
        log.warning("FPGA bridge init failed (%s) — ALSU unavailable, bitstream upload still works.", exc)
        bridge = None

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(5)
    log.info("FPGA ALSU server listening on %s:%s", host, port)
    try:
        while True:
            conn, addr = server_sock.accept()
            t = threading.Thread(target=_handle_client, args=(conn, addr, bridge), daemon=True)
            t.start()
    except KeyboardInterrupt:
        log.info("Server shutting down.")
    finally:
        server_sock.close()
        if bridge is not None:
            bridge.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FPGA ALSU Pi server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--uart-port", default="/dev/ttyUSB0",
                        help="Serial device for FPGA ALSU communication (default: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()
    run_server(host=args.host, port=args.port, uart_port=args.uart_port, baud=args.baud)
