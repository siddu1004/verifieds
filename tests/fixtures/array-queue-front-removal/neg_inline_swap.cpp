// Bubble sort with an inline temporary swap. The line a[j] = a[j + 1] looks
// like a left shift, but the loop writes back to a[j + 1], so it is an
// exchange, not a dequeue. This rule must not fire here.
void sortIt(int* a, int n) {
    for (int i = 0; i < n - 1; ++i) {
        for (int j = 0; j < n - 1 - i; ++j) {
            if (a[j] > a[j + 1]) {
                int t = a[j];
                a[j] = a[j + 1];
                a[j + 1] = t;
            }
        }
    }
}
