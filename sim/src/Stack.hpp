#ifndef SIM_STACK_HPP
#define SIM_STACK_HPP

#include "DynArray.hpp"
#include <stdexcept>

template <typename T>
class Stack {
private:
    DynArray<T> elements_;

public:
    Stack() = default;

    void push(const T& value) {
        elements_.push_back(value);
    }

    void push(T&& value) {
        elements_.push_back(std::move(value));
    }

    void pop() {
        if (empty()) {
            throw std::underflow_error("pop on empty Stack");
        }
        elements_.pop_back();
    }

    T& peek() {
        if (empty()) {
            throw std::underflow_error("peek on empty Stack");
        }
        return elements_[elements_.size() - 1];
    }

    const T& peek() const {
        if (empty()) {
            throw std::underflow_error("peek on empty Stack");
        }
        return elements_[elements_.size() - 1];
    }

    [[nodiscard]] bool empty() const noexcept {
        return elements_.empty();
    }

    [[nodiscard]] std::size_t size() const noexcept {
        return elements_.size();
    }
};

#endif // SIM_STACK_HPP
