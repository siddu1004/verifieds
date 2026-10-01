// Smoke test: verifies CMake + CTest pipeline is wired correctly.
// Replaced by real structure tests in S-01.
#include <cassert>
#include <cstdlib>

int main() {
    assert(1 + 1 == 2);  // NOLINT(cert-dcl03-c)
    return EXIT_SUCCESS;
}
