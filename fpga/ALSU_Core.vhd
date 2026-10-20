library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity ALSU_Core is
    Port ( 
        A      : in  STD_LOGIC_VECTOR (7 downto 0);
        B      : in  STD_LOGIC_VECTOR (7 downto 0);
        opcode : in  STD_LOGIC_VECTOR (2 downto 0);
        result : out STD_LOGIC_VECTOR (15 downto 0)
    );
end ALSU_Core;

architecture Behavioral of ALSU_Core is
begin
    process(A, B, opcode)
    begin
        case opcode is
            when "000" => result <= std_logic_vector(resize(unsigned(A), 16) + resize(unsigned(B), 16)); -- Add
            when "001" => result <= std_logic_vector(resize(unsigned(A), 16) - resize(unsigned(B), 16)); -- Sub
            when "010" => result <= std_logic_vector(unsigned(A) * unsigned(B));                        -- Mult
            when "011" => result <= std_logic_vector(shift_left(resize(unsigned(A), 16), to_integer(unsigned(B(2 downto 0)))));         -- Shift
            when "100" => result <= "00000000" & A;                                                     -- Bypass
            when "101" => result <= "00000000" & (A xor B);                                             -- XOR
            when others => result <= (others => '0');
        end case;
    end process;
end Behavioral;