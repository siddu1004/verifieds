int find_min_index(int* arr, int n) {
    int best = 0;
    for (int i = 1; i < n; ++i) {
        if (arr[i] < arr[best]) {
            best = i;
        }
    }
    return best;
}
