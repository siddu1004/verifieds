#ifndef SIM_DYNARRAY_HPP
#define SIM_DYNARRAY_HPP

#include <cstddef>
#include <initializer_list>
#include <stdexcept>
#include <utility>

template <typename T>
class DynArray {
private:
    T* data_;
    std::size_t size_;
    std::size_t capacity_;

    void reallocate(std::size_t new_capacity) {
        T* new_data = new T[new_capacity];
        for (std::size_t i = 0; i < size_; ++i) {
            new_data[i] = std::move(data_[i]);
        }
        delete[] data_;
        data_ = new_data;
        capacity_ = new_capacity;
    }

public:
    DynArray() : data_(nullptr), size_(0), capacity_(0) {}

    explicit DynArray(std::size_t initial_capacity)
        : data_(nullptr), size_(0), capacity_(0) {
        if (initial_capacity > 0) {
            data_ = new T[initial_capacity];
            capacity_ = initial_capacity;
        }
    }

    DynArray(std::initializer_list<T> list) : DynArray(list.size()) {
        for (const auto& item : list) {
            push_back(item);
        }
    }

    DynArray(const DynArray& other)
        : data_(nullptr), size_(other.size_), capacity_(other.capacity_) {
        if (capacity_ > 0) {
            data_ = new T[capacity_];
            for (std::size_t i = 0; i < size_; ++i) {
                data_[i] = other.data_[i];
            }
        }
    }

    DynArray(DynArray&& other) noexcept
        : data_(other.data_), size_(other.size_), capacity_(other.capacity_) {
        other.data_ = nullptr;
        other.size_ = 0;
        other.capacity_ = 0;
    }

    DynArray& operator=(const DynArray& other) {
        if (this != &other) {
            DynArray temp(other);
            swap(temp);
        }
        return *this;
    }

    DynArray& operator=(DynArray&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            capacity_ = other.capacity_;

            other.data_ = nullptr;
            other.size_ = 0;
            other.capacity_ = 0;
        }
        return *this;
    }

    ~DynArray() {
        delete[] data_;
    }

    void swap(DynArray& other) noexcept {
        std::swap(data_, other.data_);
        std::swap(size_, other.size_);
        std::swap(capacity_, other.capacity_);
    }

    [[nodiscard]] std::size_t size() const noexcept {
        return size_;
    }

    [[nodiscard]] std::size_t capacity() const noexcept {
        return capacity_;
    }

    [[nodiscard]] bool empty() const noexcept {
        return size_ == 0;
    }

    void push_back(const T& value) {
        if (size_ == capacity_) {
            reallocate(capacity_ == 0 ? 4 : capacity_ * 2);
        }
        data_[size_++] = value;
    }

    void push_back(T&& value) {
        if (size_ == capacity_) {
            reallocate(capacity_ == 0 ? 4 : capacity_ * 2);
        }
        data_[size_++] = std::move(value);
    }

    void pop_back() {
        if (empty()) {
            throw std::underflow_error("pop_back on empty DynArray");
        }
        --size_;
    }

    T& at(std::size_t index) {
        if (index >= size_) {
            throw std::out_of_range("DynArray index out of range");
        }
        return data_[index];
    }

    const T& at(std::size_t index) const {
        if (index >= size_) {
            throw std::out_of_range("DynArray index out of range");
        }
        return data_[index];
    }

    T& operator[](std::size_t index) noexcept {
        return data_[index];
    }

    const T& operator[](std::size_t index) const noexcept {
        return data_[index];
    }
};

#endif // SIM_DYNARRAY_HPP
