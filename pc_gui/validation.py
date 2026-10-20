import ipaddress


VALID_OPERATIONS = {"ADD", "SUB", "MUL", "SHIFT", "BYPASS", "XOR"}


def validate_ip(value: str) -> tuple:
    candidate = value.strip()
    if not candidate:
        return (False, "IP address is required.")
    if candidate.lower() == "localhost":
        return (True, "")
    try:
        ipaddress.IPv4Address(candidate)
    except ipaddress.AddressValueError:
        return (False, "Enter localhost or a valid IPv4 address.")
    return (True, "")


def validate_port(value: str) -> tuple:
    candidate = value.strip()
    if not candidate:
        return (False, "Port is required.")
    if not candidate.isdigit():
        return (False, "Port must be a number from 1 to 65535.")
    port = int(candidate)
    if not 1 <= port <= 65535:
        return (False, "Port must be between 1 and 65535.")
    return (True, "")


def validate_input_a(value: str) -> tuple:
    candidate = value.strip()
    if not candidate:
        return (False, "Input A is required.")
    if not candidate.isdigit():
        return (False, "Input A must contain digits only.")
    number = int(candidate)
    if not 0 <= number <= 255:
        return (False, "Input A must be between 0 and 255.")
    return (True, "")


def validate_input_b(value: str, operation: str) -> tuple:
    op = operation.strip().upper()
    if op == "BYPASS":
        return (True, "")

    candidate = value.strip()
    if not candidate:
        return (False, "Input B is required.")
    if not candidate.isdigit():
        return (False, "Input B must contain digits only.")

    number = int(candidate)
    if op == "SHIFT":
        if not 0 <= number <= 7:
            return (False, "Shift amount must be between 0 and 7.")
        return (True, "")

    if not 0 <= number <= 255:
        return (False, "Input B must be between 0 and 255.")
    return (True, "")


def validate_operation(value: str) -> tuple:
    if value.strip().upper() not in VALID_OPERATIONS:
        return (False, "Select a valid ALSU operation.")
    return (True, "")


def validate_alsu_form(op: str, a_str: str, b_str: str) -> tuple:
    validators = (
        validate_operation(op),
        validate_input_a(a_str),
        validate_input_b(b_str, op),
    )
    errors = [message for is_valid, message in validators if not is_valid]
    return (not errors, errors)
