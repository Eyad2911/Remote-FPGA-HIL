import pytest

from pc_gui.validation import (
    validate_alsu_form,
    validate_input_a,
    validate_input_b,
    validate_ip,
    validate_operation,
    validate_port,
)


class TestValidateIp:
    def test_localhost_is_valid(self):
        ok, _ = validate_ip("localhost")
        assert ok

    def test_localhost_case_insensitive(self):
        ok, _ = validate_ip("LOCALHOST")
        assert ok

    def test_valid_ipv4(self):
        ok, _ = validate_ip("192.168.1.100")
        assert ok

    def test_valid_ipv4_loopback(self):
        ok, _ = validate_ip("127.0.0.1")
        assert ok

    def test_strips_whitespace(self):
        ok, _ = validate_ip("  192.168.0.1  ")
        assert ok

    def test_empty_string_is_invalid(self):
        ok, msg = validate_ip("")
        assert not ok
        assert msg

    def test_invalid_ipv4_rejects(self):
        ok, msg = validate_ip("999.999.999.999")
        assert not ok
        assert msg

    def test_hostname_rejects(self):
        ok, msg = validate_ip("mypi.local")
        assert not ok
        assert msg

    def test_ipv6_rejects(self):
        ok, _ = validate_ip("::1")
        assert not ok


class TestValidatePort:
    def test_valid_port(self):
        ok, _ = validate_port("5000")
        assert ok

    def test_port_1_is_valid(self):
        ok, _ = validate_port("1")
        assert ok

    def test_port_65535_is_valid(self):
        ok, _ = validate_port("65535")
        assert ok

    def test_strips_whitespace(self):
        ok, _ = validate_port("  5000  ")
        assert ok

    def test_empty_is_invalid(self):
        ok, msg = validate_port("")
        assert not ok
        assert msg

    def test_zero_is_invalid(self):
        ok, _ = validate_port("0")
        assert not ok

    def test_65536_is_invalid(self):
        ok, _ = validate_port("65536")
        assert not ok

    def test_negative_is_invalid(self):
        ok, _ = validate_port("-1")
        assert not ok

    def test_letters_are_invalid(self):
        ok, msg = validate_port("abc")
        assert not ok
        assert msg


class TestValidateInputA:
    def test_zero_is_valid(self):
        ok, _ = validate_input_a("0")
        assert ok

    def test_255_is_valid(self):
        ok, _ = validate_input_a("255")
        assert ok

    def test_midrange_is_valid(self):
        ok, _ = validate_input_a("128")
        assert ok

    def test_strips_whitespace(self):
        ok, _ = validate_input_a("  10  ")
        assert ok

    def test_empty_is_invalid(self):
        ok, msg = validate_input_a("")
        assert not ok
        assert msg

    def test_256_is_invalid(self):
        ok, _ = validate_input_a("256")
        assert not ok

    def test_negative_is_invalid(self):
        ok, _ = validate_input_a("-1")
        assert not ok

    def test_float_is_invalid(self):
        ok, _ = validate_input_a("1.5")
        assert not ok

    def test_letters_are_invalid(self):
        ok, _ = validate_input_a("abc")
        assert not ok


class TestValidateInputB:
    def test_bypass_always_valid(self):
        ok, _ = validate_input_b("", "BYPASS")
        assert ok

    def test_bypass_with_any_value_valid(self):
        ok, _ = validate_input_b("999", "BYPASS")
        assert ok

    def test_zero_for_add(self):
        ok, _ = validate_input_b("0", "ADD")
        assert ok

    def test_255_for_add(self):
        ok, _ = validate_input_b("255", "ADD")
        assert ok

    def test_256_for_add_is_invalid(self):
        ok, _ = validate_input_b("256", "ADD")
        assert not ok

    def test_empty_for_add_is_invalid(self):
        ok, msg = validate_input_b("", "ADD")
        assert not ok
        assert msg

    def test_shift_0_is_valid(self):
        ok, _ = validate_input_b("0", "SHIFT")
        assert ok

    def test_shift_7_is_valid(self):
        ok, _ = validate_input_b("7", "SHIFT")
        assert ok

    def test_shift_8_is_invalid(self):
        ok, msg = validate_input_b("8", "SHIFT")
        assert not ok
        assert "7" in msg

    def test_shift_negative_is_invalid(self):
        ok, _ = validate_input_b("-1", "SHIFT")
        assert not ok


class TestValidateOperation:
    @pytest.mark.parametrize("op", ["ADD", "SUB", "MUL", "SHIFT", "BYPASS", "XOR"])
    def test_all_valid_ops(self, op):
        ok, _ = validate_operation(op)
        assert ok

    def test_lowercase_accepted(self):
        # validate_operation normalises to upper-case, so "add" == "ADD"
        ok, _ = validate_operation("add")
        assert ok

    def test_unknown_op_rejected(self):
        ok, msg = validate_operation("DIV")
        assert not ok
        assert msg

    def test_empty_rejected(self):
        ok, _ = validate_operation("")
        assert not ok


class TestValidateAlsuForm:
    def test_valid_add(self):
        ok, errors = validate_alsu_form("ADD", "10", "5")
        assert ok
        assert errors == []

    def test_valid_bypass(self):
        ok, _ = validate_alsu_form("BYPASS", "42", "")
        assert ok

    def test_valid_shift(self):
        ok, _ = validate_alsu_form("SHIFT", "4", "3")
        assert ok

    def test_invalid_op_returns_error(self):
        ok, errors = validate_alsu_form("DIV", "10", "5")
        assert not ok
        assert len(errors) >= 1

    def test_invalid_a_returns_error(self):
        ok, errors = validate_alsu_form("ADD", "300", "5")
        assert not ok
        assert errors

    def test_invalid_b_returns_error(self):
        ok, errors = validate_alsu_form("ADD", "10", "300")
        assert not ok
        assert errors

    def test_multiple_errors_collected(self):
        ok, errors = validate_alsu_form("BAD_OP", "999", "999")
        assert not ok
        assert len(errors) >= 2

    def test_boundary_add_max(self):
        ok, _ = validate_alsu_form("ADD", "255", "255")
        assert ok

    def test_shift_boundary_max(self):
        ok, _ = validate_alsu_form("SHIFT", "255", "7")
        assert ok

    def test_shift_boundary_over(self):
        ok, errors = validate_alsu_form("SHIFT", "255", "8")
        assert not ok
