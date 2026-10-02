#ifndef SIM_READYQUEUE_HPP
#define SIM_READYQUEUE_HPP

#include "DynArray.hpp"
#include "MinHeap.hpp"
#include <cstddef>
#include <stdexcept>

struct ReadyEntry {
    long key{0};
    int arrival{0};
    int pid{0};

    bool operator<(const ReadyEntry& other) const noexcept {
        if (key != other.key) return key < other.key;
        if (arrival != other.arrival) return arrival < other.arrival;
        return pid < other.pid;
    }

    bool operator==(const ReadyEntry& other) const noexcept {
        return key == other.key && arrival == other.arrival && pid == other.pid;
    }
};

class ReadyQueue {
public:
    virtual ~ReadyQueue() = default;
    virtual void push(const ReadyEntry& entry) = 0;
    virtual ReadyEntry pop_min() = 0;
    virtual const ReadyEntry& peek_min() const = 0;
    virtual bool empty() const = 0;
    virtual void clear() = 0;
};

class ArrayReadyQueue : public ReadyQueue {
private:
    DynArray<ReadyEntry> items_;

public:
    ArrayReadyQueue() = default;

    void push(const ReadyEntry& entry) override {
        items_.push_back(entry);
    }

    // Intentionally O(n) naive pop_min for detector test subject
    ReadyEntry pop_min() override {
        if (items_.empty()) {
            throw std::underflow_error("pop_min on empty ArrayReadyQueue");
        }
        std::size_t best = 0;
        for (std::size_t i = 1; i < items_.size(); ++i) {
            if (items_[i] < items_[best]) { best = i; }
        }
        ReadyEntry out = items_[best];
        for (std::size_t i = best; i + 1 < items_.size(); ++i) { items_[i] = items_[i + 1]; }
        items_.pop_back();
        return out;
    }

    const ReadyEntry& peek_min() const override {
        if (items_.empty()) {
            throw std::underflow_error("peek_min on empty ArrayReadyQueue");
        }
        std::size_t best = 0;
        for (std::size_t i = 1; i < items_.size(); ++i) {
            if (items_[i] < items_[best]) { best = i; }
        }
        return items_[best];
    }

    bool empty() const override {
        return items_.empty();
    }

    void clear() override {
        while (!items_.empty()) {
            items_.pop_back();
        }
    }
};

class HeapReadyQueue : public ReadyQueue {
private:
    MinHeap<ReadyEntry> heap_;

public:
    HeapReadyQueue() = default;

    void push(const ReadyEntry& entry) override {
        heap_.insert(entry);
    }

    ReadyEntry pop_min() override {
        return heap_.extract_min();
    }

    const ReadyEntry& peek_min() const override {
        return heap_.peek_min();
    }

    bool empty() const override {
        return heap_.empty();
    }

    void clear() override {
        while (!heap_.empty()) {
            heap_.extract_min();
        }
    }
};

#endif // SIM_READYQUEUE_HPP
