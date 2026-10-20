# Hardware Notes

## ALSU operations

The supplied `ALSU_Core.vhd` is combinational and accepts two 8-bit operands plus a 3-bit opcode. It supports:

| Opcode | Operation | Result behavior |
|---|---|---|
| `000` | ADD | Zero-extend both operands to 16 bits, then add |
| `001` | SUB | 16-bit unsigned subtraction result |
| `010` | MUL | 8-bit operands multiplied into a 16-bit result |
| `011` | SHIFT | Logical left shift of A by B(2 downto 0) |
| `100` | BYPASS | Return A, zero-extended to 16 bits |
| `101` | XOR | Bitwise XOR of A and B, zero-extended to 16 bits |

Other opcodes return zero in the supplied source.

## Controller sequence

The `HIL_Controller` state machine receives A, then B, then the opcode; gives the combinational ALSU one clock cycle to settle; sends the result high byte and then low byte; and returns to waiting for the next transaction.

## Physical wiring from the supplied constraints

- Basys 3 100 MHz clock: W5
- FPGA RX: J1 (Pmod JA1), connect to Raspberry Pi TXD / GPIO 14
- FPGA TX: L2 (Pmod JA2), connect to Raspberry Pi RXD / GPIO 15
- Share ground and maintain 3.3 V UART-level compatibility.

The report PDF was not copied into this public-ready source package because it contains named team roster/student identifiers. The technical project description above omits those personal identifiers.
