#include <unistd.h>

#define PYTHON ".\\windows\\python\\python.exe"

int main(void) {
    execl(PYTHON, PYTHON, ".\\rattrack.py", NULL);
    return 1;
}
