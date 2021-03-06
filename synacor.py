#!/usr/bin/env python3

import array
import sys
import argparse

# 0000 : intro message
# 015b : self-test
# 0375 : call routine #1 (once)
# 05b2 : routine 05b2 - reads word at [8000], calls [8001]
# 05fb : routine 05fb - outputs text
# 06bb : routine 06bb (once)
# 06cb :   call routine 084d
# 06d0 :   call routine 084d
# 0706 : in op for prompt
# 084d : routine 084d (48187 times) (decryption?)
# 154b : check for hacked H register
# 154e : text announcing that confirmation routine is starting
# 155e :   call routine 05b2
# 1566 :   5 NOPs
# 156b :   2 SETs to 8000 and 8001 -> set to 1,4
# 1571 :   call to mega-recursive confirmation routine
# 1573 :   check that 8000==6
# 158a :   call routine 05b2
# 158c :   do something with 8007!
# 15a0 :   call routine 0731
# 15e3 :   jump to function epilogue
# 1652 :   three POP's and a RET
# 178b : mega-recursive confirmation routine (it's not Ackermann is it?)
#           (that's the most evilly recursive function I know, anyhow)
#           (i'll just bet that it is! >_<)
#           A(1,4)==6
#           A(4,1)==65533=0xfffd

def opcode(c):
    def opcode(f):
        f.opcode = c
        return f
    return opcode

class Synacor:
    def __init__(self, filename):
        self.mem = self.load(filename)
        self.reg = {x: 0 for x in range(0x8000, 0x8008)}
        self.ip = 0
        self.stack = []
        self.ops = {f.__func__.opcode: (f, f.__func__.__code__.co_argcount-1)
                    for f in [getattr(self, k) for k in dir(self)]
                    if hasattr(f, '__func__') and hasattr(f.__func__, 'opcode')}
        self.debug_level = 0

    @staticmethod
    def load(filename):
        memory = array.array('H')
        with open(filename, 'rb') as f:
            memory.frombytes(f.read())
        memory.extend([0] * (0xffff-len(memory)))
        return memory

    def run(self, break_at=None):
        while 0 <= self.ip <= 0xffff:
            if break_at is not None and self.ip == break_at:
                break
            opcode = self.mem[self.ip]
            op, c = self.ops[opcode]
            args = [self.mem[offset] for offset in range(self.ip+1, self.ip+c+1)]
            next_ip = op(*args)
            if self.debug_level > 0:
                print('{0:04x}  {1:<4s}  {2:<14s}  {3}  {4}'.format(
                    self.ip,
                    op.__name__[3:],
                    ' '.join('{:04x}'.format(a) for a in args),
                    ' '.join('{}={:04x}'.format(k, self.reg[v]) for (k, v) in zip('abcdefgh', range(0x8000, 0x8008))),
                    '' if op != self.op_out else repr(chr(self[self.mem[self.ip+1]]))
                ), file=sys.stderr, flush=False)
            self.ip = next_ip if next_ip is not None else self.ip+c+1

    def dump_memory(self):
        for i in range(0, len(M), 8):
            print('{:08x} {:04x} {:04x} {:04x} {:04x} {:04x} {:04x} {:04x} {:04x}'.format(i, *[M[i+x] for x in range(8)]))

    def disassemble(self):
        ip = 0
        while ip < len(self.mem):
            try:
                op, c = self.ops[self.mem[ip]]
                args = ['{0:04x}'.format(self.mem[offset]) for offset in range(ip+1, ip+c+1)]
                print('{0:04x}  {1:<4s}  {2:<14s}  {3}'.format(
                    ip,
                    op.__name__[3:],
                    ' '.join(args),
                    '' if op != self.op_out else repr(chr(self[self.mem[ip+1]]))))
                ip += 1+c
            except KeyError:
                print('{0:04x}  {1:<4s}  {2:04x}  {3}'.format(
                    ip,
                    'dw',
                    self.mem[ip],
                    repr(chr(self.mem[ip])) if 32 <= self.mem[ip] < 128 else ''))
                ip += 1

    def poke(self, offset, *values):
        for (i, v) in enumerate(values):
            self.mem[offset+i] = v

    def __getitem__(self, k):
        return self.reg.get(k, k)

    def __setitem__(self, k, v):
        if not (0x8000 <= k < 0x8008):
            raise ValueError('invalid register {:04x}'.format(k))
        self.reg[k] = v

    @opcode(0x00)
    def op_halt(self):
        return -1

    @opcode(0x01)
    def op_set(self, a, b):
        self[a] = self[b]

    @opcode(0x02)
    def op_push(self, a):
        self.stack.append(self[a])

    @opcode(0x03)
    def op_pop(self, a):
        if not self.stack:
            raise RuntimeError('stack is empty')
        self[a] = self.stack.pop()

    @opcode(0x04)
    def op_eq(self, a, b, c):
        self[a] = 1 if self[b] == self[c] else 0

    @opcode(0x05)
    def op_gt(self, a, b, c):
        self[a] = 1 if self[b] > self[c] else 0

    @opcode(0x06)
    def op_jmp(self, a):
        return self[a]

    @opcode(0x07)
    def op_jt(self, a, b):
        return self[b] if self[a] != 0 else None

    @opcode(0x08)
    def op_jf(self, a, b):
        return self[b] if self[a] == 0 else None

    @opcode(0x09)
    def op_add(self, a, b, c):
        self[a] = (self[b] + self[c]) % 0x8000

    @opcode(0x0a)
    def op_mult(self, a, b, c):
        if b == 6 and c == 9 and 0: # set to 1 to trigger 'not hitchhiking' self-test error :-)
            self[a] = 42
            return
        self[a] = (self[b] * self[c]) % 0x8000

    @opcode(0x0b)
    def op_mod(self, a, b, c):
        self[a] = self[b] % self[c]

    @opcode(0x0c)
    def op_and(self, a, b, c):
        self[a] = self[b] & self[c]

    @opcode(0x0d)
    def op_or(self, a, b, c):
        self[a] = self[b] | self[c]

    @opcode(0x0e)
    def op_not(self, a, b):
        self[a] = self[b] ^ 0x7fff

    @opcode(0x0f)
    def op_rmem(self, a, b):
        self[a] = self.mem[self[b]]

    @opcode(0x10)
    def op_wmem(self, a, b):
        self.mem[self[a]] = self[b]

    @opcode(0x11)
    def op_call(self, a):
        self.stack.append(self.ip+2)
        return self[a]

    @opcode(0x12)
    def op_ret(self):
        if not self.stack:
            raise RuntimeError('stack is empty')
        return self.stack.pop()

    @opcode(0x13)
    def op_out(self, a):
        sys.stdout.write(chr(self[a]))
        sys.stdout.flush()

    @opcode(0x14)
    def op_in(self, a):
        c = sys.stdin.read(1)
        if not c:
            return -1
        self[a] = ord(c)

    @opcode(0x15)
    def op_noop(self):
        pass

#---

def test_load_file_1(): assert list(load('challenge.bin')[:3]) == [21,21,19]
def test_load_file_2(): assert len(load('challenge.bin')) == 65535

#---

def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='the .bin file to load')
    parser.add_argument('--debug', '-d', action='count', default=0, help='debug level')
    parser.add_argument('--breakpoint', action='store', default=None, help='break at hexadecimal address')
    parser.add_argument('--poke', action='store', nargs='+', help='hexadecimal numbers, first is address, rest is machine code')
    group = parser.add_mutually_exclusive_group()

    group.add_argument('--dump', action='store_true', help='output memory dump')
    group.add_argument('--disasm', action='store_true', help='output disassembly')
    return parser.parse_args(args)

def main(args):
    args = parse_args(args)
    #print(args)
    synacor = Synacor(args.filename)
    synacor.debug_level = args.debug
    if args.poke:
        for values in args.poke:
            synacor.poke(*[int(x, 16) for x in values.split()])
    if args.breakpoint is not None:
        synacor.run(break_at=int(args.breakpoint, 16))
    if args.dump:
        synacor.dump_memory()
    elif args.disasm:
        synacor.disassemble()
    else:
        synacor.run()

if __name__ == '__main__':
    main(sys.argv[1:])
