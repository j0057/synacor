# Synacor challenge

VM and debugging tools for the [Synacor challenge](https://challenge.synacor.com/).

## My war story so far...

...and the bugs I made, as I recall them.

I started with reading [arch-spec](./arch-spec), and entered the first code. I
added the hexadecimal numbers for the opcodes to the document, to make reading
the output of `hexdump -C challenge.bin` a little bit easier. Then I started
hacking on the VM, just a bunch of Python functions. I looked at Python's
`struct` module to read the binary file, but that's for structs. Luckily Python
also has the `array` module, which is just perfect for reading a blob of 16-bit
unsigned integers into a list-like object.

The first iteration of this code was good enough to get me past the intro,
sadly I didn't commit it to Git. It had a list of `(operation_function,
argument_count)` tuples, and a `run` function that used opcodes as indexes
into the list of opcode tuples. Because I had an off-by-one error in this list,
opcode 1 got interpreted as the halt instruction, and I got a little stuck in the
self-test.

Then I refactored the functions to a class -- I've always loved how Python
scales with my understanding of a problem. I wanted to get rid of the list of
tuples, so my first thought was to use a decorator to register each opcode
implementation into some registry. I first wanted to implement this decorator
as a `@classmethod` in the class itself, but it turns out that during creation
of a class, the decorated function isn't yet a function, but a `classmethod`
object, and it's not until the class creation is finished that the classmethod
is actually a callable method. So I had to implement the opcode decorator
outside of the class, in a loose function (I'll probably refactor it into a
base class).

During the implementation of the rest of the opcodes required to pass the
self-test, I implemented `__getitem__` and `__setitem__` to resolve numbers to
registry or literal values. After the self-test passed, I did a little more
refactoring, to pull out the `ip` and `stack` into proper members.

The opcode registry thing did get rid of the off-by-one bug where opcode 1 was
was executed as `halt` instead of `set`.

I know dungeon crawlers from back in the day, and wasn't really feeling like
playing yet another one, so I looked into reverse engineering the dungeon layout.
I made liberal use of the debug output, as well as `grep`, `awk`, `sort -u` and
`wc -l` to get a sense of the jumps and the loops:

    grep '\(jmp\|jt\|jf\|call\|ret\)' debug.log | less

But after an hour or so of this, I decided to do it the old-fashioned way, not
with pencil, paper and eraser this time, but [a map drawn by
Graphviz](./dungeon.svg).

## Codes

These are the codes and where/how I found them:

1. *NxUWWNvLaYEn* - just RTFM in arch-spec
2. *RTpCEKDxvICs* - from the intro message
3. *euAPXBMMORJj* - completion of the self-test
4. *MijBfgCMdHFe* - from the tablet in the foothills
5. *dqEiLlHwactH* - from the twisty little maze of passages, all alike
6. *MIwLffGealdt* - from the teleporter
7. *TfTWmqpRlMsk* - from the hacked teleporter
8. *VUuYHqI8IlHX* - from the mirror

    ./synacor.py --poke '0209 0001 8007 0001' '156b 0001 8000 0001 0001 8001 0004' -- challenge.bin <dungeon.txt

    >>> [(a,b,c,d,e) for (a,b,c,d,e) in itertools.permutations([2,3,5,7,9]) if a+b*c**2+d**3-e==399]
    [(9, 2, 5, 7, 3)]
