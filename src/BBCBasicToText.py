#!/usr/bin/env python
#
# (c) 2007 Matt Godbolt.
# Use however you like, as long as you put credit where credit's due.
# Some information obtained from source code from RISC OS Open.
# v0.01 - first release.  Doesn't deal with GOTO line numbers.

import struct, re, getopt, sys

# The list of BBC BASIC V tokens:
# Base tokens, starting at 0x7f
tokens = [
    b'OTHERWISE', # 7f
    b'AND', b'DIV', b'EOR', b'MOD', b'OR', b'ERROR', b'LINE', b'OFF',
    b'STEP', b'SPC', b'TAB(', b'ELSE', b'THEN', b'<line>' # TODO
        , b'OPENIN', b'PTR',

    b'PAGE', b'TIME', b'LOMEM', b'HIMEM', b'ABS', b'ACS', b'ADVAL', b'ASC',
    b'ASN', b'ATN', b'BGET', b'COS', b'COUNT', b'DEG', b'ERL', b'ERR',

    b'EVAL', b'EXP', b'EXT', b'FALSE', b'FN', b'GET', b'INKEY', b'INSTR(',
    b'INT', b'LEN', b'LN', b'LOG', b'NOT', b'OPENUP', b'OPENOUT', b'PI',

    b'POINT(', b'POS', b'RAD', b'RND', b'SGN', b'SIN', b'SQR', b'TAN',
    b'TO', b'TRUE', b'USR', b'VAL', b'VPOS', b'CHR$', b'GET$', b'INKEY$',

    b'LEFT$(', b'MID$(', b'RIGHT$(', b'STR$', b'STRING$(', b'EOF',
        b'<ESCFN>', b'<ESCCOM>', b'<ESCSTMT>',
    b'WHEN', b'OF', b'ENDCASE', b'ELSE' # ELSE2
        , b'ENDIF', b'ENDWHILE', b'PTR',

    b'PAGE', b'TIME', b'LOMEM', b'HIMEM', b'SOUND', b'BPUT', b'CALL', b'CHAIN',
    b'CLEAR', b'CLOSE', b'CLG', b'CLS', b'DATA', b'DEF', b'DIM', b'DRAW',

    b'END', b'ENDPROC', b'ENVELOPE', b'FOR', b'GOSU', b'GOTO', b'GCOL', b'IF',
    b'INPUT', b'LET', b'LOCAL', b'MODE', b'MOVE', b'NEXT', b'ON', b'VDU',

    b'PLOT', b'PRINT', b'PROC', b'READ', b'REM', b'REPEAT', b'REPORT', b'RESTORE',
    b'RETURN', b'RUN', b'STOP', b'COLOUR', b'TRACE', b'UNTIL', b'WIDTH', b'OSCLI']

# Referred to as "ESCFN" tokens in the source, starting at 0x8e.
cfnTokens = [
    b'SUM', b'BEAT']
# Referred to as "ESCCOM" tokens in the source, starting at 0x8e.
comTokens = [
    b'APPEND', b'AUTO', b'CRUNCH', b'DELET', b'EDIT', b'HELP', b'LIST', b'LOAD',
    b'LVAR', b'NEW', b'OLD', b'RENUMBER', b'SAVE', b'TEXTLOAD', b'TEXTSAVE', b'TWIN',
    b'TWINO', b'INSTALL']
# Referred to as "ESCSTMT", starting at 0x8e.
stmtTokens= [
    b'CASE', b'CIRCLE', b'FILL', b'ORIGIN', b'PSET', b'RECT', b'SWAP', b'WHILE',
    b'WAIT', b'MOUSE', b'QUIT', b'SYS', b'INSTALL', b'LIBRARY', b'TINT', b'ELLIPSE',
    b'BEATS', b'TEMPO', b'VOICES', b'VOICE', b'STEREO', b'OVERLAY']

def DetokeniseOld(line):
    """Replace all tokens in the line 'line' with their ASCII equivalent."""
    # Internal function used as a callback to the regular expression
    # to replace tokens with their ASCII equivalents.
    def ReplaceFunc(match):
        ext, token = match.groups()
        tokenOrd = token[0] #ord(token[0])
        if ext: # An extended opcode, CASE/WHILE/SYS etc
            if ext == '\xc6':
                return cfnTokens[tokenOrd-0x8e]
            if ext == '\xc7':
                return comTokens[tokenOrd-0x8e]
            if ext == '\xc8':
                return stmtTokens[tokenOrd-0x8e]
            raise Exception("Bad token")
        else: # Normal token, plus any extra characters
            return tokens[tokenOrd-127] + token[1:]

    # This regular expression is essentially:
    # (Optional extension token) followed by
    # (REM token followed by the rest of the line)
    #     -- this ensures we don't detokenise the REM statement itself
    # OR
    # (any token)
    return re.sub(r'([\xc6-\xc8])?(\xf4.*|[\x7f-\xff])', ReplaceFunc, line)

def Detokenise(line):
    """Replace all tokens in the line 'line' with their ASCII equivalent."""
    # Internal function used as a callback to the regular expression
    # to replace tokens with their ASCII equivalents.
    
    detoken = True
    index = 0
    size = len(line)
    result = bytearray()

    while index < size:
        data = line[index]
        if (data >= 0x7F) and detoken:
            result += tokens[data - 127]
        else:
            result += bytearray([data])
        if data == ord('"'):
            detoken = not detoken
        index += 1

    return result

def ReadLines(data):
    """Returns a list of [line number, tokenised line] from a binary
       BBC BASIC V format file."""
    lines = []
    while True:
        if len(data) < 2:
            raise Exception("Bad program")
        if data[0] != 13: #'\r':
            print(data)
            raise Exception("Bad program")
        if data[1] == 0xff:
            break
        lineNumber, length = struct.unpack('>hB', data[1:4])
        lineData = data[4:length]
        lines.append([lineNumber, lineData])
        data = data[length:]
    return lines

def Decode(data, output, use_line_numbers=True):
    """Decode binary data 'data' and write the result to 'output'."""
    lines = ReadLines(data)
    for lineNumber, line in lines:
        lineData = bytes(f"{lineNumber} ", encoding='utf8') if use_line_numbers else bytes()
        lineData += Detokenise(line)
        output.write(lineData + bytearray([13]))

if __name__ == "__main__":
    optlist, args = getopt.getopt(sys.argv[1:], '')
    if len(args) != 2:
        print("Usage: %s INPUT OUTPUT" % sys.argv[0])
        sys.exit(1)
    with open(args[0], 'rb') as file_in:
        entireFile = file_in.read()
        with open(args[1], 'wb') as file_out:
            Decode(entireFile, file_out)
