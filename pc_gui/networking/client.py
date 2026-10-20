import os
import socket
import threading
from typing import Callable, Optional

from pc_gui.networking.protocol import (
    ProtocolError,
    alsu_packet,
    encode_message,
    file_packet,
    ping_packet,
    recv_message,
)

_CONNECT_TIMEOUT = 5.0
_RECV_TIMEOUT = 5.0
_UPLOAD_TIMEOUT = 60.0  # FPGA programming can take a while


class NetworkClient:
    def __init__(
        self,
        result_callback: Callable,
        log_callback: Callable,
        connection_lost_callback: Optional[Callable] = None,
    ) -> None:
        self._result_cb = result_callback
        self._log_cb = log_callback
        self._connection_lost_cb = connection_lost_callback
        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()

    # ── Connection ─────────────────────────────────────────────────────────────

    def connect(self, ip: str, port: int) -> bool:
        with self._lock:
            if self._sock is not None:
                self._log_cb("Already connected — disconnect first.")
                return False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(_CONNECT_TIMEOUT)
            sock.connect((ip.strip(), int(port)))
            sock.settimeout(_RECV_TIMEOUT)
            with self._lock:
                self._sock = sock
            self._log_cb(f"TCP connection established to {ip.strip()}:{port}")
            return True
        except socket.timeout:
            self._log_cb(f"Connection timed out after {_CONNECT_TIMEOUT}s.")
        except ConnectionRefusedError:
            self._log_cb(f"Connection refused by {ip.strip()}:{port} — is the server running?")
        except OSError as exc:
            self._log_cb(f"Connection error: {exc}")
        return False

    def disconnect(self) -> None:
        with self._lock:
            sock = self._sock
            self._sock = None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass
            self._log_cb("TCP connection closed.")
        else:
            self._log_cb("Already disconnected.")

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._sock is not None

    # ── Commands ───────────────────────────────────────────────────────────────

    def send_ping(self) -> bool:
        response = self._send_recv(ping_packet())
        return isinstance(response, dict) and response.get("status") == "ok"

    def send_alsu_request(self, operation: str, a: int, b: int) -> Optional[int]:
        response = self._send_recv(alsu_packet(operation, a, b))
        if response is None:
            return None
        if response.get("status") == "error":
            self._log_cb(f"Server ALSU error: {response.get('message', 'unknown')}")
            return None
        if "result" in response:
            return int(response["result"])
        self._log_cb("Server returned an unexpected ALSU response.")
        return None

    def send_bitstream(
        self,
        filepath: str,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> bool:
        if not os.path.isfile(filepath):
            self._log_cb(f"Bitstream file not found: {filepath!r}")
            return False

        # Read the file (10 %)
        if progress_callback:
            progress_callback(10)
        with open(filepath, "rb") as fh:
            data = fh.read()
        filename = os.path.basename(filepath)
        self._log_cb(f"Read {len(data):,} bytes from {filename}")

        # Build packet (30 %)
        msg = file_packet(filename, data)
        if progress_callback:
            progress_callback(30)

        # Send with extended timeout for FPGA programming (50 %)
        with self._lock:
            sock = self._sock
        if sock is None:
            self._log_cb("Cannot send bitstream — not connected.")
            return False

        try:
            sock.settimeout(_UPLOAD_TIMEOUT)
            sock.sendall(encode_message(msg))
            if progress_callback:
                progress_callback(60)

            self._log_cb("Bitstream sent — waiting for FPGA programming to finish...")
            response = recv_message(sock)
            sock.settimeout(_RECV_TIMEOUT)  # restore normal timeout

            if progress_callback:
                progress_callback(100)

            if response.get("status") == "ok":
                self._log_cb(f"FPGA programmed: {response.get('message', 'OK')}")
                return True
            else:
                self._log_cb(f"Upload failed: {response.get('message', 'unknown error')}")
                return False

        except socket.timeout:
            self._log_cb("Bitstream upload timed out.")
        except ProtocolError as exc:
            self._log_cb(f"Protocol error during upload: {exc}")
        except OSError as exc:
            self._log_cb(f"Network error during upload: {exc}")

        self._close_broken_socket()
        return False

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _send_recv(self, msg: dict) -> Optional[dict]:
        with self._lock:
            sock = self._sock
        if sock is None:
            self._log_cb("Cannot send — not connected.")
            return None
        try:
            sock.sendall(encode_message(msg))
            return recv_message(sock)
        except socket.timeout:
            self._log_cb("Request timed out — server did not respond in time.")
        except ProtocolError as exc:
            self._log_cb(f"Protocol error: {exc}")
        except OSError as exc:
            self._log_cb(f"Network error during send/recv: {exc}")
        self._close_broken_socket()
        return None

    def _close_broken_socket(self) -> None:
        with self._lock:
            sock = self._sock
            self._sock = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
            if self._connection_lost_cb:
                self._connection_lost_cb()
