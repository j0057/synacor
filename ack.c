
#include <stdio.h>

int A(int m, int n) {
    if (m == 0)
        return (n+1) % 32768;
    else if (n == 0)
        return A(m-1, 1);
    else
        return A(m-1, A(m, n-1));
}

int main(int argc, char *argv[]) {
    int r = A(4, 1);
    printf("%d %x\n", r, r);
}
