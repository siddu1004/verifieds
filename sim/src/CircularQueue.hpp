#ifndef SIM_CIRCULARQUEUE_HPP
#define SIM_CIRCULARQUEUE_HPP

#include <cstddef>
#include <stdexcept>
#include <utility>

template <typename T>
class CircularQueue {
private:
    T* data_;
    std::size_t head_;
    std::size_t tail_;
    std::size_t size_;
    std::size_t capacity_;

    void resize(std::size_t new_capacity) {
        T* new_data = new T[new_capacity];
        for (std::size_t i = 0; i < size_; ++i) {
            new_data[i] = std::move(data_[(head_ + i) % capacity_]);
        }
        delete[] data_;
        data_ = new_data;
        head_ = 0;
        tail_ = size_;
        capacity_ = new_capacity;
    }

public:
    explicit CircularQueue(std::size_t initial_capacity = 4)
        : data_(new T[initial_capacity]), head_(0), tail_(0), size_(0), capacity_(initial_capacity) {}

    CircularQueue(const CircularQueue& other)
        : data_(new T[other.capacity_]),
          head_(0),
          tail_(other.size_),
          size_(other.size_),
          capacity_(other.capacity_) {
        for (std::size_t i = 0; i < size_; ++i) {
            data_[i] = other.data_[(other.head_ + i) % other.capacity_];
        }
    }

    CircularQueue(CircularQueue&& other) noexcept
        : data_(other.data_),
          head_(other.head_),
          tail_(other.tail_),
          size_(other.size_),
          capacity_(other.capacity_) {
        other.data_ = nullptr;
        other.head_ = 0;
        other.tail_ = 0;
        other.size_ = 0;
        other.capacity_ = 0;
    }

    CircularQueue& operator=(const CircularQueue& other) {
        if (this != &other) {
            CircularQueue temp(other);
            swap(temp);
        }
        return *this;
    }

    CircularQueue& operator=(CircularQueue&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            head_ = other.head_;
            tail_ = other.tail_;
            size_ = other.size_;
            capacity_ = other.capacity_;

            other.data_ = nullptr;
            other.head_ = 0;
            other.tail_ = 0;
            other.size_ = 0;
            other.capacity_ = 0;
        }
        return *this;
    }

    ~CircularQueue() {
        delete[] data_;
    }

    void swap(CircularQueue& other) noexcept {
        std::swap(data_, other.data_);
        std::swap(head_, other.head_);
        std::swap(tail_, other.tail_);
        std::swap(size_, other.size_);
        std::swap(capacity_, other.capacity_);
    }

    void enqueue(const T& value) {
        if (size_ == capacity_) {
            resize(capacity_ * 2);
        }
        data_[tail_] = value;
        tail_ = (tail_ + 1) % capacity_;
        ++size_;
    }

    void enqueue(T&& value) {
        if (size_ == capacity_) {
            resize(capacity_ * 2);
        }
        data_[tail_] = std::move(value);
        tail_ = (tail_ + 1) % capacity_;
        ++size_;
    }

    void dequeue() {
        if (empty()) {
            throw std::underflow_error("dequeue on empty CircularQueue");
        }
        head_ = (head_ + 1) % capacity_;
        --size_;
    }

    T& front() {
        if (empty()) {
            throw std::underflow_error("front on empty CircularQueue");
        }
        return data_[head_];
    }

    const T& front() const {
        if (empty()) {
            throw std::underflow_error("front on empty CircularQueue");
        }
        return data_[head_];
    }

    [[nodiscard]] bool empty() const noexcept {
        return size_ == 0;
    }

    [[nodiscard]] std::size_t size() const noexcept {
        return size_;
    }

    [[nodiscard]] std::size_t capacity() const noexcept {
        return capacity_;
    }
};

#endif // SIM_CIRCULARQUEUE_HPP
