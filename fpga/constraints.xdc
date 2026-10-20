## Clock signal (100MHz)
set_property PACKAGE_PIN W5 [get_ports clk]							
	set_property IOSTANDARD LVCMOS33 [get_ports clk]

## Pmod Header JA (Connecting to Raspberry Pi 5)
## Pin 1 (JA1) -> FPGA RX (Connect to Pi TX - GPIO 14)
set_property PACKAGE_PIN J1 [get_ports rx]					
	set_property IOSTANDARD LVCMOS33 [get_ports rx]
## Pin 2 (JA2) -> FPGA TX (Connect to Pi RX - GPIO 15)
set_property PACKAGE_PIN L2 [get_ports tx]					
	set_property IOSTANDARD LVCMOS33 [get_ports tx]