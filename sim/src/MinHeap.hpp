#ifndef SIM_MINHEAP_HPP
#define SIM_MINHEAP_HPP

#include "DynArray.hpp"
#include <cstddef>
#include <stdexcept>
#include <utility>

template <typename T>
class MinHeap {
private:
    DynArray<T> heap_;

    void heapify_up(std::size_t index) {
        while (index > 0) {
            std::size_t parent = (index - 1) / 2;
            if (heap_[index] < heap_[parent]) {
                std::swap(heap_[index], heap_[parent]);
                index = parent;
            } else {
                break;
            }
        }
    }

    void heapify_down(std::size_t index) {
        std::size_t size = heap_.size();
        while (true) {
            std::size_t smallest = index;
            std::size_t left = 2 * index + 1;
            std::size_t right = 2 * index + 2;

            if (left < size && heap_[left] < heap_[smallest]) {
                smallest = left;
            }
            if (right < size && heap_[right] < heap_[smallest]) {
                smallest = right;
            }

            if (smallest != index) {
                std::swap(heap_[index], heap_[smallest]);
                index = smallest;
            } else {
                break;
            }
        }
    }

public:
    MinHeap() = default;

    void insert(const T& value) {
        heap_.push_back(value);
        heapify_up(heap_.size() - 1);
    }

    void insert(T&& value) {
        heap_.push_back(std::move(value));
        heapify_up(heap_.size() - 1);
    }

    T extract_min() {
        if (empty()) {
            throw std::underflow_error("extract_min on empty MinHeap");
        }
        T min_val = std::move(heap_[0]);
        heap_[0] = std::move(heap_[heap_.size() - 1]);
        heap_.pop_back();
        if (!empty()) {
            heapify_down(0);
        }
        return min_val;
    }

    const T& peek_min() const {
        if (empty()) {
            throw std::underflow_error("peek_min on empty MinHeap");
        }
        return heap_[0];
    }

    [[nodiscard]] bool empty() const noexcept {
        return heap_.empty();
    }

    [[nodiscard]] std::size_t size() const noexcept {
        return heap_.size();
    }

    static void heap_sort(DynArray<T>& arr) {
        MinHeap<T> h;
        for (std::size_t i = 0; i < arr.size(); ++i) {
            h.insert(arr[i]);
        }
        for (std::size_t i = 0; i < arr.size(); ++i) {
            arr[i] = h.extract_min();
        }
    }
};

#endif // SIM_MINHEAP_HPP
