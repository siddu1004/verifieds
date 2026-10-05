#ifndef SIM_SORT_HPP
#define SIM_SORT_HPP

#include "DynArray.hpp"
#include <cstddef>
#include <utility>

template <typename T, typename Compare>
void merge_sort(DynArray<T>& arr, std::size_t left, std::size_t right, Compare comp) {
    if (left >= right) return;
    std::size_t mid = left + (right - left) / 2;
    merge_sort(arr, left, mid, comp);
    merge_sort(arr, mid + 1, right, comp);

    DynArray<T> temp;
    std::size_t i = left;
    std::size_t j = mid + 1;

    while (i <= mid && j <= right) {
        if (!comp(arr[j], arr[i])) { // arr[i] <= arr[j] for stability
            temp.push_back(arr[i++]);
        } else {
            temp.push_back(arr[j++]);
        }
    }
    while (i <= mid) temp.push_back(arr[i++]);
    while (j <= right) temp.push_back(arr[j++]);

    for (std::size_t k = 0; k < temp.size(); ++k) {
        arr[left + k] = temp[k];
    }
}

template <typename T, typename Compare>
void stable_sort(DynArray<T>& arr, Compare comp) {
    if (arr.size() <= 1) return;
    merge_sort(arr, 0, arr.size() - 1, comp);
}

#endif // SIM_SORT_HPP
