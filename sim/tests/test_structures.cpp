#include "DynArray.hpp"
#include "Stack.hpp"
#include "CircularQueue.hpp"
#include "MinHeap.hpp"
#include "BST.hpp"

#include <algorithm>
#include <cassert>
#include <iostream>
#include <random>
#include <vector>

void test_dynarray() {
    DynArray<int> arr;
    assert(arr.empty());
    assert(arr.size() == 0);

    for (int i = 0; i < 100; ++i) {
        arr.push_back(i);
    }
    assert(arr.size() == 100);
    assert(arr.capacity() >= 100);
    assert(arr.at(50) == 50);

    for (int i = 99; i >= 0; --i) {
        assert(arr[static_cast<std::size_t>(i)] == i);
        arr.pop_back();
    }
    assert(arr.empty());

    bool exception_caught = false;
    try {
        arr.pop_back();
    } catch (const std::underflow_error&) {
        exception_caught = true;
    }
    assert(exception_caught);
}

void test_stack() {
    Stack<int> s;
    assert(s.empty());

    bool exception_caught_pop = false;
    try {
        s.pop();
    } catch (const std::underflow_error&) {
        exception_caught_pop = true;
    }
    assert(exception_caught_pop);

    bool exception_caught_peek = false;
    try {
        s.peek();
    } catch (const std::underflow_error&) {
        exception_caught_peek = true;
    }
    assert(exception_caught_peek);

    s.push(10);
    s.push(20);
    assert(s.peek() == 20);
    s.pop();
    assert(s.peek() == 10);
    s.pop();
    assert(s.empty());
}

void test_circular_queue() {
    CircularQueue<int> q(2);
    assert(q.empty());

    q.enqueue(1);
    q.enqueue(2);
    q.enqueue(3); // triggers capacity growth
    assert(q.size() == 3);
    assert(q.front() == 1);

    q.dequeue();
    assert(q.front() == 2);
    q.dequeue();
    assert(q.front() == 3);
    q.dequeue();
    assert(q.empty());

    bool exception_caught = false;
    try {
        q.dequeue();
    } catch (const std::underflow_error&) {
        exception_caught = true;
    }
    assert(exception_caught);
}

void test_min_heap_and_heap_sort() {
    MinHeap<int> heap;
    assert(heap.empty());

    heap.insert(5);
    heap.insert(1);
    heap.insert(3);
    assert(heap.peek_min() == 1);
    assert(heap.extract_min() == 1);
    assert(heap.extract_min() == 3);
    assert(heap.extract_min() == 5);
    assert(heap.empty());

    // 1,000 seeded random inputs benchmark vs std::sort (reference test only)
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(-5000, 5000);

    DynArray<int> arr;
    std::vector<int> ref;

    for (int i = 0; i < 1000; ++i) {
        int val = dist(rng);
        arr.push_back(val);
        ref.push_back(val);
    }

    MinHeap<int>::heap_sort(arr);
    std::sort(ref.begin(), ref.end());

    for (std::size_t i = 0; i < 1000; ++i) {
        assert(arr[i] == ref[i]);
    }
}

void test_bst() {
    BST<int> tree;
    assert(tree.empty());

    // Insert elements
    tree.insert(50);
    tree.insert(30);
    tree.insert(70);
    tree.insert(20);
    tree.insert(40);
    tree.insert(60);
    tree.insert(80);

    assert(tree.size() == 7);
    assert(tree.search(40));
    assert(!tree.search(99));

    // Traversals
    DynArray<int> in = tree.in_order();
    assert(in.size() == 7);
    for (std::size_t i = 1; i < in.size(); ++i) {
        assert(in[i - 1] <= in[i]);
    }

    // Delete node with 0 children (leaf 20)
    assert(tree.remove(20));
    assert(!tree.search(20));
    assert(tree.size() == 6);

    // Delete node with 1 child (30 has child 40)
    assert(tree.remove(30));
    assert(!tree.search(30));
    assert(tree.search(40));
    assert(tree.size() == 5);

    // Delete node with 2 children (root 50)
    assert(tree.remove(50));
    assert(!tree.search(50));
    assert(tree.size() == 4);
    assert(tree.search(40));
    assert(tree.search(70));
}

int main() {
    test_dynarray();
    test_stack();
    test_circular_queue();
    test_min_heap_and_heap_sort();
    test_bst();
    std::cout << "All S-01 structure tests passed successfully!\n";
    return 0;
}
