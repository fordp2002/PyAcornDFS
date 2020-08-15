''' Decode BBC Basic Programs '''

def key_word_table():
    ''' Basic Keywords '''
    token = []

    def KeyWord(text, flags):
        ''' Parse a Keyword '''
        token.append({"text": text, "flags": flags})
        if flags:
            if flags & 0x20:
                print(text, flags)

    # 0x00 to 0x7F
    for _index in range(0x80):
        KeyWord(None, None)

    # 0x80
    KeyWord("AND",	0x00)
    KeyWord("DIV",	0x00)
    KeyWord("EOR",	0x00)
    KeyWord("MOD",	0x00)
    KeyWord("OR",	0x00)
    KeyWord("ERROR",0x04)
    KeyWord("LINE",	0x00)
    KeyWord("OFF",	0x00)

    # 0x88
    KeyWord("STEP",	0x00)
    KeyWord("SPC",	0x00)
    KeyWord("TAB(",	0x00)
    KeyWord("ELSE",	0x14)
    KeyWord("THEN",	0x14)
    KeyWord("",		0x00)
    KeyWord("OPENIN",0x00)
    KeyWord("PTR",	0x43)

    # 0x90
    KeyWord("PAGE",	0x43)
    KeyWord("TIME",	0x43)
    KeyWord("LOMEM",0x43)
    KeyWord("HIMEM",0x43)
    KeyWord("ABS",	0x00)
    KeyWord("ACS",	0x00)
    KeyWord("ADVAL",0x00)
    KeyWord("ASC",	0x00)

    # 0x98
    KeyWord("ASN",	0x00)
    KeyWord("ATN",	0x00)
    KeyWord("BGET",	0x01)
    KeyWord("COS",	0x00)
    KeyWord("COUNT",0x01)
    KeyWord("DEG",	0x00)
    KeyWord("ERL",	0x01)
    KeyWord("ERR",	0x01)

    # 0xa0
    KeyWord("EVAL",	0x00)
    KeyWord("EXP",	0x00)
    KeyWord("EXT",	0x01)
    KeyWord("FALSE",0x01)
    KeyWord("FN",	0x08)
    KeyWord("GET",	0x00)
    KeyWord("INKEY",0x00)
    KeyWord("INSTR(",0x00)

    # 0xa8
    KeyWord("INT",	0x00)
    KeyWord("LEN",	0x00)
    KeyWord("LN",	0x00)
    KeyWord("LOG",	0x00)
    KeyWord("NOT",	0x00)
    KeyWord("OPENUP",0x00)
    KeyWord("OPENOUT",0x00)
    KeyWord("PI",	0x01)

    # 0xb0
    KeyWord("POINT(",0x00)
    KeyWord("POS",	0x01)
    KeyWord("RAD",	0x00)
    KeyWord("RND",	0x01)
    KeyWord("SGN",	0x00)
    KeyWord("SIN",	0x00)
    KeyWord("SQR",	0x00)
    KeyWord("TAN",	0x00)

    # 0xb8
    KeyWord("TO",	0x00)
    KeyWord("TRUE",	0x01)
    KeyWord("USR",	0x00)
    KeyWord("VAL",	0x00)
    KeyWord("VPOS",	0x01)
    KeyWord("CHR$",	0x00)
    KeyWord("GET$",	0x00)
    KeyWord("INKEY$",0x00)

    # 0xc0
    KeyWord("LEFT$(",0x00)
    KeyWord("MID$(",0x00)
    KeyWord("RIGHT$(",0x00)
    KeyWord("STR$",	0x00)
    KeyWord("STRING$(",0x00)
    KeyWord("EOF",	0x01)
    KeyWord("AUTO",	0x10)
    KeyWord("DELETE",0x10)

    # 0xc8
    KeyWord("LOAD",	0x02)
    KeyWord("LIST",	0x10)
    KeyWord("NEW",	0x01)
    KeyWord("OLD",	0x01)
    KeyWord("RENUMBER",0x10)
    KeyWord("SAVE",	0x02)
    KeyWord("",		0x00)
    KeyWord("PTR",	0x00)

    # 0xd0
    KeyWord("PAGE",	0x00)
    KeyWord("TIME",	0x01)
    KeyWord("LOMEM",0x00)
    KeyWord("HIMEM",0x00)
    KeyWord("SOUND",0x02)
    KeyWord("BPUT",	0x03)
    KeyWord("CALL",	0x02)
    KeyWord("CHAIN",0x02)

    # 0xd8
    KeyWord("CLEAR",0x01)
    KeyWord("CLOSE",0x03)
    KeyWord("CLG",	0x01)
    KeyWord("CLS",	0x01)
    KeyWord("DATA",	0x20)
    KeyWord("DEF",	0x00)
    KeyWord("DIM",	0x02)
    KeyWord("DRAW",	0x02)

    # 0xe0
    KeyWord("END",	0x01)
    KeyWord("ENDPROC",0x01)
    KeyWord("ENVELOPE",0x02)
    KeyWord("FOR",	0x02)
    KeyWord("GOSUB",0x12)
    KeyWord("GOTO",	0x12)
    KeyWord("GCOL",	0x02)
    KeyWord("IF",	0x02)

    # 0xe8
    KeyWord("INPUT",0x02)
    KeyWord("LET",	0x04)
    KeyWord("LOCAL",0x02)
    KeyWord("MODE",	0x02)
    KeyWord("MOVE",	0x02)
    KeyWord("NEXT",	0x02)
    KeyWord("ON",	0x02)
    KeyWord("VDU",	0x02)

    # 0xf0
    KeyWord("PLOT",	0x02)
    KeyWord("PRINT",0x02)
    KeyWord("PROC",	0x0a)
    KeyWord("READ",	0x02)
    KeyWord("REM",	0x20)
    KeyWord("REPEAT",0x00)
    KeyWord("REPORT",0x01)
    KeyWord("RESTORE",0x12)

    # 0xf8
    KeyWord("RETURN",0x01)
    KeyWord("RUN",	0x01)
    KeyWord("STOP",	0x01)
    KeyWord("COLOUR",0x02)
    KeyWord("TRACE",0x12)
    KeyWord("UNTIL",0x02)
    KeyWord("WIDTH",0x02)
    KeyWord("OSCLI",0x02)

    return token

def debug():
    token = key_word_table()
    for index in range(0x100):        
        if index >= 0x80:
            if index < 0xC0:
                value = token[index]['text'] == token[index + 0x40]['text']
                if value:
                    print(f"{index:02X} {token[index]['text']} {token[index + 0x40]['text']}")
                    continue
            print(f"{index:02X} {token[index]['text']:8s} {token[index]['flags']:02X}")                        

def extract_line(data, result, addr, line_length):
    ''' Export a single basic line '''
    def get_byte():
        ''' Get the next byte '''
        value = data[addr]
        addr += 1
        line_length -= 1
        return value

    while line_length >=0:
        this_byte = get_byte()
         
        if this_byte >= 0x80:
            if this_byte == 0x8D:
                value = get_byte()
                line_number = (value & 0x0C) << 12
                line_number += (value & 0x30) << 2
                line_number += get_byte() & 0x3F
                line_number += get_byte() << 8
                line_number ^= 0x4040
                result += f"{line_number}"
            else:
                result += TOKEN[this_byte]["text"]
                if TOKEN[this_byte]["flags"] & 0x20:
                    while line_length:
                        result += str(get_byte())
                    return True
        else:
            if this_byte == '"':
                result += '"'
                while data[addr] != '"' and line_length >= 0:
                        result += str(get_byte())
                if data[addr] == '"':
                        result += str(get_byte())
            else:
                result += str(get_byte())
    return True if line_length == -1 else False

def export_basic(data, filename):
    ''' Export basic from a byte array '''
    error_num = 0
    result = ""

    addr = data[0x18] << 8  # Get the value of PAGE, start reading BASIC code from there

    if addr >= (32768 - 4):
        error_num = 6

    while error_num == 0:
        if data[addr] != 0x0D:
            error_num = 5
            break

        addr += 1
        line_number = (data[addr] << 8) + data[addr + 1]
        addr += 2
        if  line_number & 0x8000:
            break
        line_length =data[addr]
        addr += 1

        if addr + line_length > (32768 - 4):
            error_num = 6
            break

        result += f"{line_number:5d}"

        if not extract_line(data, result, addr, line_length):
            break

        result += '\n'

        addr += line_length - 4
        
    if error_num == 0:
        with open(filename, "wt") as file_p:
            file_p.write(result)
    return error_num

TOKEN = key_word_table()

if __name__ == "__main__":    
    debug()
