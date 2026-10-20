library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity UART_TX is
    Generic (
        CLKS_PER_BIT : integer := 868     -- 100MHz / 115200 baud
    );
    Port (
        clk         : in  STD_LOGIC;
        tx_data_in  : in  STD_LOGIC_VECTOR(7 downto 0);
        tx_start    : in  STD_LOGIC;
        tx_serial   : out STD_LOGIC;
        tx_busy     : out STD_LOGIC
    );
end UART_TX;

architecture Behavioral of UART_TX is
    type state_type is (IDLE, START_BIT, DATA_BITS, STOP_BIT, CLEANUP);
    signal state : state_type := IDLE;
    
    signal clk_count : integer range 0 to CLKS_PER_BIT-1 := 0;
    signal bit_index : integer range 0 to 7 := 0;
    signal tx_data   : STD_LOGIC_VECTOR(7 downto 0) := (others => '0');
begin
    process(clk)
    begin
        if rising_edge(clk) then
            case state is
                when IDLE =>
                    tx_serial <= '1'; -- Drive line high for idle
                    tx_busy   <= '0';
                    clk_count <= 0;
                    bit_index <= 0;
                    if tx_start = '1' then
                        tx_data <= tx_data_in;
                        state <= START_BIT;
                    end if;
                    
                when START_BIT =>
                    tx_busy <= '1';
                    tx_serial <= '0'; -- Send Start Bit
                    if clk_count = CLKS_PER_BIT - 1 then
                        clk_count <= 0;
                        state <= DATA_BITS;
                    else
                        clk_count <= clk_count + 1;
                    end if;
                    
                when DATA_BITS =>
                    tx_serial <= tx_data(bit_index);
                    if clk_count = CLKS_PER_BIT - 1 then
                        clk_count <= 0;
                        if bit_index = 7 then
                            state <= STOP_BIT;
                        else
                            bit_index <= bit_index + 1;
                        end if;
                    else
                        clk_count <= clk_count + 1;
                    end if;
                    
                when STOP_BIT =>
                    tx_serial <= '1'; -- Send Stop Bit
                    if clk_count = CLKS_PER_BIT - 1 then
                        clk_count <= 0;
                        state <= CLEANUP;
                    else
                        clk_count <= clk_count + 1;
                    end if;
                    
                when CLEANUP =>
                    tx_busy <= '0';
                    state <= IDLE;
            end case;
        end if;
    end process;
end Behavioral;