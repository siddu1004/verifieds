#include <utility>

void bubble_sort_while(int* arr, int n) {
    int i = 0;
    while (i < n) {
        int j = 0;
        while (j < n - 1) {
            if (arr[j] > arr[j + 1]) {
                std::swap(arr[j], arr[j + 1]);
            }
            j++;
        }
        i++;
    }
}
