# Creates a C lookup table for Unicode case folding (https://unicode.org/Public/UCD/latest/ucd/CaseFolding.txt).
# Usage: python3 tools/make_case_fold_inc.py < data/CaseFolding.txt > src/case_fold.inc

import sys, re

prog = re.compile('([0-9A-F]+); [CF];((?: [0-9A-F]+)+);')
main_table = []
repl_table = []
repl_idx = 0
test = ''
test_result = ''

for line in sys.stdin:
    m = prog.match(line)
    if m is None:
        continue

    cp = int(m[1], 16);
    if cp < 0x80:
        continue

    repl = b''
    for x in m[2].split():
        repl += chr(int(x, 16)).encode('UTF-8')

    # Generate test case
    if len(main_table) % 20 == 0:
        test += chr(cp)
        test_result += repl.decode('UTF-8')

    # 17 bits for code point
    if cp >= (1 << 17):
        raise Exception("code point too large")

    # 12 bits for upper bits of replacement index
    # The lowest bit is always zero.
    if repl_idx // 2 >= (1 << 12):
        raise Exception("too many replacements")

    # 3 bits for size of replacement
    repl_size = len(repl)
    if repl_size >= (1 << 3):
        raise Exception("too many replacement chars")

    main_table += [ cp | repl_idx // 2 << 17 | repl_size << 29 ]
    repl_table += repl
    repl_idx += repl_size

    # Make sure that repl_idx is even
    if repl_idx % 2 != 0:
        repl_table += [0]
        repl_idx += 1

# Print test case
if False:
    print("test:", test)
    print("test_result:", test_result)
    sys.exit(0)

print("""// Generated by tools/make_case_fold_inc.py

#define CF_MAX            (1 << 17)
#define CF_TABLE_SIZE     %d
#define CF_CODE_POINT(x)  ((x) & 0x1FFFF)
#define CF_REPL_IDX(x)    ((((x) >> 17) & 0xFFF) * 2)
#define CF_REPL_SIZE(x)   ((x) >> 29)

static const uint32_t cf_table[%d] = {""" % (len(main_table), len(main_table)))

i = 0
size = len(main_table)
for value in main_table:
    if i % 6 == 0:
        print("  ", end="")
    print("0x%X" % value, end="")
    i += 1
    if i == size: print()
    elif i % 6 == 0: print(",")
    else: print(", ", end="")

print("""};

static const unsigned char cf_repl[%d] = {""" % len(repl_table))

i = 0
size = len(repl_table)
for value in repl_table:
    if i % 12 == 0:
        print("  ", end="")
    print("0x%02X" % value, end="")
    i += 1
    if i == size: print()
    elif i % 12 == 0: print(",")
    else: print(", ", end="")

print("};")
