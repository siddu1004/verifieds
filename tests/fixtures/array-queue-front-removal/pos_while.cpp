void pop_front_while(int* arr, int n) {
    int i = 0;
    while (i < n - 1) {
        arr[i] = arr[i + 1];
        i++;
    }
}
