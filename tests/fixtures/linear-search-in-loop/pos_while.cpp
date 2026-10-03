int linear_search_while(int* arr, int n, int key) {
    int outer = 0;
    while (outer < 5) {
        int j = 0;
        while (j < n) {
            if (arr[j] == key) {
                return j;
            }
            j++;
        }
        outer++;
    }
    return -1;
}
