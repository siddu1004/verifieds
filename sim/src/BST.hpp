#ifndef SIM_BST_HPP
#define SIM_BST_HPP

#include "DynArray.hpp"
#include <cstddef>
#include <utility>

template <typename T>
class BST {
private:
    struct Node {
        T data;
        Node* left;
        Node* right;

        explicit Node(const T& val) : data(val), left(nullptr), right(nullptr) {}
        explicit Node(T&& val) : data(std::move(val)), left(nullptr), right(nullptr) {}
    };

    Node* root_;
    std::size_t size_;

    Node* insert_rec(Node* node, const T& val) {
        if (node == nullptr) {
            ++size_;
            return new Node(val);
        }
        if (val < node->data) {
            node->left = insert_rec(node->left, val);
        } else {
            node->right = insert_rec(node->right, val);
        }
        return node;
    }

    Node* find_min(Node* node) const noexcept {
        while (node != nullptr && node->left != nullptr) {
            node = node->left;
        }
        return node;
    }

    Node* remove_rec(Node* node, const T& val, bool& removed) {
        if (node == nullptr) {
            return nullptr;
        }
        if (val < node->data) {
            node->left = remove_rec(node->left, val, removed);
        } else if (node->data < val) {
            node->right = remove_rec(node->right, val, removed);
        } else {
            // Found node to delete
            removed = true;
            // Case 1: 0 children (leaf)
            if (node->left == nullptr && node->right == nullptr) {
                delete node;
                return nullptr;
            }
            // Case 2: 1 child
            if (node->left == nullptr) {
                Node* temp = node->right;
                delete node;
                return temp;
            }
            if (node->right == nullptr) {
                Node* temp = node->left;
                delete node;
                return temp;
            }
            // Case 3: 2 children
            const Node* successor = find_min(node->right);
            node->data = successor->data;
            node->right = remove_rec(node->right, successor->data, removed);
        }
        return node;
    }

    bool search_rec(Node* node, const T& val) const noexcept {
        if (node == nullptr) {
            return false;
        }
        if (val < node->data) {
            return search_rec(node->left, val);
        }
        if (node->data < val) {
            return search_rec(node->right, val);
        }
        return true;
    }

    void in_order_rec(Node* node, DynArray<T>& result) const {
        if (node != nullptr) {
            in_order_rec(node->left, result);
            result.push_back(node->data);
            in_order_rec(node->right, result);
        }
    }

    void pre_order_rec(Node* node, DynArray<T>& result) const {
        if (node != nullptr) {
            result.push_back(node->data);
            pre_order_rec(node->left, result);
            pre_order_rec(node->right, result);
        }
    }

    void post_order_rec(Node* node, DynArray<T>& result) const {
        if (node != nullptr) {
            post_order_rec(node->left, result);
            post_order_rec(node->right, result);
            result.push_back(node->data);
        }
    }

    void destroy(Node* node) noexcept {
        if (node != nullptr) {
            destroy(node->left);
            destroy(node->right);
            delete node;
        }
    }

public:
    BST() : root_(nullptr), size_(0) {}

    ~BST() {
        destroy(root_);
    }

    BST(const BST&) = delete;
    BST& operator=(const BST&) = delete;

    BST(BST&& other) noexcept : root_(other.root_), size_(other.size_) {
        other.root_ = nullptr;
        other.size_ = 0;
    }

    BST& operator=(BST&& other) noexcept {
        if (this != &other) {
            destroy(root_);
            root_ = other.root_;
            size_ = other.size_;
            other.root_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    void insert(const T& val) {
        root_ = insert_rec(root_, val);
    }

    bool remove(const T& val) {
        bool removed = false;
        root_ = remove_rec(root_, val, removed);
        if (removed) {
            --size_;
        }
        return removed;
    }

    [[nodiscard]] bool search(const T& val) const noexcept {
        return search_rec(root_, val);
    }

    [[nodiscard]] DynArray<T> in_order() const {
        DynArray<T> result;
        in_order_rec(root_, result);
        return result;
    }

    [[nodiscard]] DynArray<T> pre_order() const {
        DynArray<T> result;
        pre_order_rec(root_, result);
        return result;
    }

    [[nodiscard]] DynArray<T> post_order() const {
        DynArray<T> result;
        post_order_rec(root_, result);
        return result;
    }

    [[nodiscard]] bool empty() const noexcept {
        return size_ == 0;
    }

    [[nodiscard]] std::size_t size() const noexcept {
        return size_;
    }
};

#endif // SIM_BST_HPP
