int linear_search(int* arr, int n, int key) {
    for (int i = 0; i < 10; ++i) {
        for (int j = 0; j < n; ++j) {
            if (arr[j] == key) {
                return j;
            }
        }
    }
    return -1;
}
