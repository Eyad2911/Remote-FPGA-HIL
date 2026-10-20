library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity UART_RX is
    Generic (
        CLKS_PER_BIT : integer := 868     -- 100MHz / 115200 baud
    );
    Port (
        clk           : in  STD_LOGIC;
        rx_serial     : in  STD_LOGIC;
        rx_data_out   : out STD_LOGIC_VECTOR(7 downto 0);
        rx_data_ready : out STD_LOGIC
    );
end UART_RX;

architecture Behavioral of UART_RX is
    type state_type is (IDLE, START_BIT, DATA_BITS, STOP_BIT, CLEANUP);
    signal state : state_type := IDLE;
    
    signal clk_count : integer range 0 to CLKS_PER_BIT-1 := 0;
    signal bit_index : integer range 0 to 7 := 0;
    signal rx_data   : STD_LOGIC_VECTOR(7 downto 0) := (others => '0');
begin
    process(clk)
    begin
        if rising_edge(clk) then
            case state is
                when IDLE =>
                    rx_data_ready <= '0';
                    clk_count <= 0;
                    bit_index <= 0;
                    if rx_serial = '0' then  -- Start bit detected
                        state <= START_BIT;
                    end if;
                    
                when START_BIT =>
                    if clk_count = (CLKS_PER_BIT - 1) / 2 then
                        if rx_serial = '0' then
                            clk_count <= 0;
                            state <= DATA_BITS;
                        else
                            state <= IDLE;
                        end if;
                    else
                        clk_count <= clk_count + 1;
                    end if;
                    
                when DATA_BITS =>
                    if clk_count = CLKS_PER_BIT - 1 then
                        clk_count <= 0;
                        rx_data(bit_index) <= rx_serial;
                        if bit_index = 7 then
                            state <= STOP_BIT;
                        else
                            bit_index <= bit_index + 1;
                        end if;
                    else
                        clk_count <= clk_count + 1;
                    end if;
                    
                when STOP_BIT =>
                    if clk_count = CLKS_PER_BIT - 1 then
                        rx_data_out <= rx_data;
                        rx_data_ready <= '1';
                        clk_count <= 0;
                        state <= CLEANUP;
                    else
                        clk_count <= clk_count + 1;
                    end if;
                    
                when CLEANUP =>
                    rx_data_ready <= '0';
                    state <= IDLE;
            end case;
        end if;
    end process;
end Behavioral;