import sys
import types

# Keep PC-only test installs usable without pyserial; hardware installs use real pyserial.
try:
    import serial  # noqa: F401
except ModuleNotFoundError:
    fake_serial_module = types.ModuleType("serial")

    class SerialException(Exception):
        pass

    fake_serial_module.SerialException = SerialException
    fake_serial_module.Serial = object
    sys.modules["serial"] = fake_serial_module

import pytest
from pi_server import fpga_bridge


class FakeSerial:
    def __init__(self, response: bytes):
        self.response = bytearray(response)
        self.writes = []
        self.closed = False

    @property
    def in_waiting(self):
        return len(self.response)

    def reset_input_buffer(self):
        pass

    def write(self, payload):
        self.writes.append(payload)
        return len(payload)

    def flush(self):
        pass

    def read(self, size=1):
        result = bytes(self.response[:size])
        del self.response[:size]
        return result

    def close(self):
        self.closed = True


@pytest.mark.parametrize(
    ("operation", "opcode"),
    [("ADD", 0), ("SUB", 1), ("MUL", 2), ("SHIFT", 3), ("BYPASS", 4), ("XOR", 5)],
)
def test_compute_sends_three_byte_request_and_reads_big_endian_result(monkeypatch, operation, opcode):
    fake = FakeSerial(b"\x12\x34")
    monkeypatch.setattr(fpga_bridge.serial, "Serial", lambda port, baud, timeout: fake)

    bridge = fpga_bridge.FPGABridge(port="/dev/test", baud=115200)
    result = bridge.compute(operation, 10, 3)

    assert fake.writes == [bytes((10, 3, opcode))]
    assert result == 0x1234


def test_shift_rejects_amount_above_seven(monkeypatch):
    fake = FakeSerial(b"\x00\x00")
    monkeypatch.setattr(fpga_bridge.serial, "Serial", lambda port, baud, timeout: fake)
    bridge = fpga_bridge.FPGABridge()

    with pytest.raises(fpga_bridge.FPGABridgeError, match="0 to 7"):
        bridge.compute("SHIFT", 10, 8)


def test_missing_response_is_not_replaced_with_software_fallback(monkeypatch):
    fake = FakeSerial(b"")
    monkeypatch.setattr(fpga_bridge.serial, "Serial", lambda port, baud, timeout: fake)
    monkeypatch.setattr(fpga_bridge, "_RESPONSE_TIMEOUT", 0.01)
    bridge = fpga_bridge.FPGABridge()

    with pytest.raises(fpga_bridge.FPGABridgeError, match="2-byte FPGA ALSU result"):
        bridge.compute("ADD", 10, 5)
