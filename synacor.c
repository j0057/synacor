
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

struct vm_t {
    uint16_t *code;
    uint16_t *stack;
    int code_size;
    int stack_size;
};

#define A *(ip+1)
#define B *(ip+2)
#define C *(ip+3)

#define s(v) reg[v^0x8000]
#define r(v) (v&0x8000 ? s(v) : v)

#define CHK_SP_MIN if (sp == vm->stack) { fprintf(stderr, "error: stack is empty at %04x\n", (uint16_t)(ip-vm->code)); return 1; }
#define CHK_SP_MAX if (sp == sp_max)    { fprintf(stderr, "error: stack is full at %04x\n",  (uint16_t)(ip-vm->code)); return 1; }

int execute(struct vm_t *vm, int debug) {
    const char *op_name[22] = { "halt", "set", "push", "pop", "eq", "gt", "jmp", "jt",
                                "jf", "add", "mult", "mod", "and", "or", "not", "rmem",
                                "wmem", "call", "ret", "out", "in", "noop" };
    const int arg_count[22] = { 0, 2, 1, 1, 3, 3, 1, 2,
                                2, 3, 3, 3, 3, 3, 2, 2,
                                2, 1, 0, 1, 1, 0 };

    uint16_t reg[8] = {0, 0, 0, 0, 0, 0, 0, 0};

    uint16_t *ip = vm->code;
    uint16_t *ip_max = vm->code + vm->code_size - 1;

    uint16_t *sp = vm->stack;
    uint16_t *sp_max = vm->stack + vm->stack_size - 1;

    while (vm->code <= ip && ip < ip_max) {
        if (debug) {
            switch (arg_count[*ip]) {
                case 0: fprintf(stderr, "%04x  %-4s                \n", (uint16_t)(ip-vm->code), op_name[*ip]);          break;
                case 1: fprintf(stderr, "%04x  %-4s  %04x          \n", (uint16_t)(ip-vm->code), op_name[*ip], A);       break;
                case 2: fprintf(stderr, "%04x  %-4s  %04x %04x     \n", (uint16_t)(ip-vm->code), op_name[*ip], A, B);    break;
                case 3: fprintf(stderr, "%04x  %-4s  %04x %04x %04x\n", (uint16_t)(ip-vm->code), op_name[*ip], A, B, C); break;
            }
        }

        switch (*ip) {
            case 0x00: /* halt */       return 0;
            case 0x01: /* set a b */    s(A) = r(B);                            ip += 3; break;
            case 0x02: /* push a */     CHK_SP_MAX; *sp++ = r(A);               ip += 2; break;
            case 0x03: /* pop a */      CHK_SP_MIN; s(A) = *--sp;               ip += 2; break;
            case 0x04: /* eq a b c */   s(A) = r(B) == r(C) ? 1 : 0;            ip += 4; break;
            case 0x05: /* gt a b c */   s(A) = r(B) >  r(C) ? 1 : 0;            ip += 4; break;
            case 0x06: /* jmp a */      ip = vm->code + r(A);                            break;
            case 0x07: /* jt a b */     ip =  r(A) ? vm->code + r(B) : ip+3;             break;
            case 0x08: /* jf a b */     ip = !r(A) ? vm->code + r(B) : ip+3;             break;
            case 0x09: /* add a b c */  s(A) = (r(B) + r(C)) & 0x7fff;          ip += 4; break; 
            case 0x0a: /* mult a b c */ s(A) = (r(B) * r(C)) & 0x7fff;          ip += 4; break; 
            case 0x0b: /* mod a b c */  s(A) = r(B) % r(C);                     ip += 4; break; 
            case 0x0c: /* and a b c */  s(A) = r(B) & r(C);                     ip += 4; break; 
            case 0x0d: /* or a b c */   s(A) = r(B) | r(C);                     ip += 4; break; 
            case 0x0e: /* not a b */    s(A) = r(B) ^ 0x7fff;                   ip += 3; break; 
            case 0x10: /* wmem a b */   *(vm->code + r(A)) = r(B);              ip += 3; break; 
            case 0x0f: /* rmem a b */   s(A) = *(vm->code + r(B));              ip += 3; break; 
            case 0x11: /* call a */     CHK_SP_MAX; *sp++ = ip-vm->code+2;      ip = vm->code + r(A); break;
            case 0x12: /* ret */        CHK_SP_MIN; ip = vm->code + *--sp;               break;
            case 0x13: /* out a */      printf("%c", r(A));                     ip += 2; break;
            case 0x14: /* in a */     { char ch;
                                        int count = fread(&ch, 1, sizeof(ch), stdin);
                                        if (count == 0) {
                                            return 0;
                                        }
                                        s(A) = (uint16_t)ch;                    ip += 2; break; }
            case 0x15: /* noop */                                               ip += 1; break;
            default:                    fprintf(stderr, "error: unrecognized instruction %#04x!\n", *ip);
                                        return 1;
        }
    }

    return 0;
}

#undef A
#undef B
#undef C

#undef s
#undef r

int poke_code(struct vm_t *vm, char *pokes[], int poke_max) {
    for (int i = 0; i < poke_max && pokes[i]; i++) {
        uint16_t *dest = NULL;
        char *next = NULL;
        for (char *value = strtok_r(pokes[i], " ", &next); value != NULL; value = strtok_r(NULL, " ", &next)) {
            char *end = NULL;
            uint16_t word = strtoul(value, &end, 16);
            if (end == value || *end != '\0') {
                fprintf(stderr, "error: cannot parse value '%s'\n", value);
                return 1;
            }
            if (dest == NULL) {
                dest = vm->code + word;
            }
            else {
                *dest++ = word;
            }
        }
    }
    return 0;
}

int load_program(struct vm_t *vm, char *filename) {
    FILE *fp = fopen(filename, "rb");

    if (fp == NULL) {
        fprintf(stderr, "error: failed to open %s\n", filename);
        return 1;
    }

    uint16_t *offset = vm->code;
    int count;
    do {
        count = fread(offset, 1, vm->code_size-(offset-vm->code), fp);
        offset += count;
    } while (count && (offset-vm->code) < vm->code_size);

    return 0;
}

void free_vm(struct vm_t *vm) {
    free(vm->code);
    free(vm->stack);
    memset(vm, 0, sizeof(struct vm_t));
}

int init_vm(struct vm_t *vm) {
    vm->code_size = sizeof(uint16_t) * 0x8000;
    vm->code = malloc(vm->code_size);
    if (!vm->code) {
        goto error;
    }
    memset(vm->code, 0, vm->code_size);

    vm->stack_size = sizeof(uint16_t) * 0x80000;
    vm->stack = malloc(vm->stack_size);
    if (!vm->stack) {
        goto error;
    }
    memset(vm->stack, 0, vm->stack_size);

    return 0;

error:
    free_vm(vm);
    return 1;
}

int parse_options(int argc, char *argv[], char **filename, char *pokes[], int max_pokes, int *debug) {
    int opt;
    int poke_index = 0;
    while ((opt = getopt(argc, argv, "-p:d")) > -1) {
        switch (opt) {
            case 0x01:
                if (*filename != NULL) {
                    fprintf(stderr, "error: more than one filename specified\n");
                    return 1;
                }
                *filename = optarg;
                continue;
            case 'd':
                *debug = 1;
                continue;
            case 'p':
                if (poke_index == max_pokes - 1) {
                    fprintf(stderr, "error: more than %d pokes\n", max_pokes);
                    return 1;
                }
                pokes[poke_index++] = optarg;
                continue;
            case '?':
                return 1;
        }
    }

    if (*filename == NULL) {
        fprintf(stderr, "error: missing filename\n");
        return 1;
    }

    return 0;
}

int main(int argc, char *argv[]) {
    char *filename = NULL;
    char *pokes[16] = {0};
    int debug = 0;

    // parse options
    if (parse_options(argc, argv, &filename, pokes, sizeof(pokes), &debug)) {
        return 1;
    }

    // initialize vm memory
    struct vm_t vm = {0};
    if (init_vm(&vm)) {
        return 2;
    }

    // load program from file
    if (load_program(&vm, filename)) {
        goto error;
    }

    // poke memory if so requested
    if (poke_code(&vm, pokes, sizeof(pokes))) {
        goto error;
    }

    // run the code
    if (execute(&vm, debug)) {
        goto error;
    }

    // clean exit
    free_vm(&vm);
    return 0;

error:
    // error exit
    free_vm(&vm);
    return 1;
}
