library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity HIL_Controller is
    Port ( 
        clk : in  STD_LOGIC;
        rx  : in  STD_LOGIC;
        tx  : out STD_LOGIC
    );
end HIL_Controller;

architecture Structural of HIL_Controller is

    -- State Machine States
    type state_type is (WAIT_A, WAIT_B, WAIT_OP, CALC_WAIT, SEND_HIGH, WAIT_TX_HIGH, SEND_LOW, WAIT_TX_LOW);
    signal state : state_type := WAIT_A;

    -- UART RX Signals
    signal rx_data_out   : STD_LOGIC_VECTOR(7 downto 0);
    signal rx_data_ready : STD_LOGIC;

    -- UART TX Signals
    signal tx_data_in    : STD_LOGIC_VECTOR(7 downto 0);
    signal tx_start      : STD_LOGIC := '0';
    signal tx_busy       : STD_LOGIC;

    -- ALSU Signals
    signal alsu_A        : STD_LOGIC_VECTOR(7 downto 0) := (others => '0');
    signal alsu_B        : STD_LOGIC_VECTOR(7 downto 0) := (others => '0');
    signal alsu_op       : STD_LOGIC_VECTOR(2 downto 0) := (others => '0');
    signal alsu_res      : STD_LOGIC_VECTOR(15 downto 0);

begin

    -- Instantiate UART Receiver
    UART_RX_Inst: entity work.UART_RX
        port map(
            clk           => clk,
            rx_serial     => rx,
            rx_data_out   => rx_data_out,
            rx_data_ready => rx_data_ready
        );

    -- Instantiate UART Transmitter
    UART_TX_Inst: entity work.UART_TX
        port map(
            clk        => clk,
            tx_data_in => tx_data_in,
            tx_start   => tx_start,
            tx_serial  => tx,
            tx_busy    => tx_busy
        );

    -- Instantiate ALSU Core
    ALSU_Inst: entity work.ALSU_Core
        port map(
            A      => alsu_A,
            B      => alsu_B,
            opcode => alsu_op,
            result => alsu_res
        );

    -- Main State Machine Process
    process(clk)
    begin
        if rising_edge(clk) then
            -- Default assignment to prevent accidental latches
            tx_start <= '0';
            
            case state is
                -- Receive Input A
                when WAIT_A =>
                    if rx_data_ready = '1' then
                        alsu_A <= rx_data_out;
                        state <= WAIT_B;
                    end if;
                    
                -- Receive Input B
                when WAIT_B =>
                    if rx_data_ready = '1' then
                        alsu_B <= rx_data_out;
                        state <= WAIT_OP;
                    end if;
                    
                -- Receive Opcode
                when WAIT_OP =>
                    if rx_data_ready = '1' then
                        alsu_op <= rx_data_out(2 downto 0);
                        state <= CALC_WAIT;
                    end if;
                    
                -- Wait 1 clock cycle for asynchronous logic to settle
                when CALC_WAIT =>
                    state <= SEND_HIGH;
                    
                -- Initiate transmission of High Byte (Bits 15 downto 8)
                when SEND_HIGH =>
                    if tx_busy = '0' then
                        tx_data_in <= alsu_res(15 downto 8);
                        tx_start <= '1';
                        state <= WAIT_TX_HIGH;
                    end if;

                -- Wait for High Byte to finish transmitting
                when WAIT_TX_HIGH =>
                    if tx_busy = '0' and tx_start = '0' then
                        state <= SEND_LOW;
                    end if;
                    
                -- Initiate transmission of Low Byte (Bits 7 downto 0)
                when SEND_LOW =>
                    if tx_busy = '0' then
                        tx_data_in <= alsu_res(7 downto 0);
                        tx_start <= '1';
                        state <= WAIT_TX_LOW;
                    end if;

                -- Wait for Low Byte to finish transmitting before resetting
                when WAIT_TX_LOW =>
                    if tx_busy = '0' and tx_start = '0' then
                        state <= WAIT_A; -- Transaction complete, wait for next input
                    end if;

            end case;
        end if;
    end process;

end Structural;