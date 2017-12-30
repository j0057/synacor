#!/usr/bin/env python3

import array
import sys
import argparse

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

    def run(self):
        while 0 <= self.ip <= 0xffff:
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
                ), file=sys.stderr, flush=True)
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
                print('{0:04x}  {1:<4s}  {2:04x}'.format(ip, 'dw', self.mem[ip]))
                ip += 1

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
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dump', action='store_true', help='output memory dump')
    group.add_argument('--disasm', action='store_true', help='output disassembly')
    return parser.parse_args(args)

def main(args):
    args = parse_args(args)
    synacor = Synacor(args.filename)
    synacor.debug_level = args.debug
    if args.dump:
        synacor.dump_memory()
    elif args.disasm:
        synacor.disassemble()
    else:
        synacor.run()

if __name__ == '__main__':
    main(sys.argv[1:])
