int find_min_while(int* arr, int n) {
    int best = 0;
    int i = 1;
    while (i < n) {
        if (arr[i] < arr[best]) {
            best = i;
        }
        i++;
    }
    return best;
}
