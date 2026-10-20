"""UART bridge matching the included HIL_Controller VHDL protocol.

Request: three UART bytes [operand A, operand B, opcode].
Response: two bytes [result high byte, result low byte].
"""
import time
import serial

OPCODES = {
    "ADD": 0b000,
    "SUB": 0b001,
    "MUL": 0b010,
    "SHIFT": 0b011,
    "BYPASS": 0b100,
    "XOR": 0b101,
}
_DEFAULT_UART_PORT = "/dev/ttyAMA0"
_DEFAULT_BAUD_RATE = 115200
_RESPONSE_TIMEOUT = 2.0


class FPGABridgeError(Exception):
    """Raised when an ALSU request cannot be completed over UART."""


class FPGABridge:
    def __init__(self, port: str = _DEFAULT_UART_PORT, baud: int = _DEFAULT_BAUD_RATE):
        self._ser = serial.Serial(port, baud, timeout=0)

    def compute(self, operation: str, a: int, b: int) -> int:
        op = str(operation).strip().upper()
        if op not in OPCODES:
            raise FPGABridgeError(f"Unknown operation: {operation!r}")
        if isinstance(a, bool) or not isinstance(a, int) or not 0 <= a <= 255:
            raise FPGABridgeError("Operand A must be an integer from 0 to 255.")
        if isinstance(b, bool) or not isinstance(b, int) or not 0 <= b <= 255:
            raise FPGABridgeError("Operand B must be an integer from 0 to 255.")
        if op == "SHIFT" and b > 7:
            raise FPGABridgeError("SHIFT operand B must be from 0 to 7.")

        # HIL_Controller captures A, B and the low 3 opcode bits as three UART bytes.
        payload = bytes((a, b, OPCODES[op]))
        try:
            self._ser.reset_input_buffer()
            self._ser.write(payload)
            self._ser.flush()
        except serial.SerialException as exc:
            raise FPGABridgeError(f"UART write error: {exc}") from exc

        raw = self._read_response()
        if len(raw) != 2:
            raise FPGABridgeError(
                f"Timed out waiting for the 2-byte FPGA ALSU result; received {len(raw)} byte(s)."
            )
        return int.from_bytes(raw, byteorder="big", signed=False)

    def _read_response(self) -> bytes:
        """Collect exactly the high and low result bytes before the timeout."""
        deadline = time.monotonic() + _RESPONSE_TIMEOUT
        buf = bytearray()
        try:
            while len(buf) < 2 and time.monotonic() < deadline:
                waiting = self._ser.in_waiting
                if waiting:
                    chunk = self._ser.read(min(waiting, 2 - len(buf)))
                    if chunk:
                        buf.extend(chunk)
                else:
                    time.sleep(0.005)
        except serial.SerialException as exc:
            raise FPGABridgeError(f"UART read error: {exc}") from exc
        return bytes(buf)

    def close(self):
        self._ser.close()
