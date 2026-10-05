struct P { int key; };
int findMin(P* a, int n) {
    int m = 0;
    for (int j = 1; j < n; ++j) {
        if (a[j].key < a[m].key) m = j;
    }
    return m;
}
