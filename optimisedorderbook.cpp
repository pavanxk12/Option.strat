#include <iostream>
#include <stdexcept>
#include <algorithm>
#include <array>
#include <cassert>

// Constants
constexpr int RING_BUFFER_SIZE = 5;
constexpr int AVL_TREE_MAX_NODES = 100;

// Ring Buffer class with Structure of Arrays (SoA) and Preallocated Memory
class RingBuffer {
private:
    struct MarketData {
        int price;
        int quantity;
    };

    std::array<int, RING_BUFFER_SIZE> prices;      // Preallocated array for prices
    std::array<int, RING_BUFFER_SIZE> quantities;  // Preallocated array for quantities
    int head;
    int tail;
    int maxSize;
    int currentSize;

public:
    RingBuffer() : head(0), tail(0), maxSize(RING_BUFFER_SIZE), currentSize(0) {}

    void insert(int price, int quantity) {
        if (currentSize == maxSize) {
            head = (head + 1) % maxSize;  // Overwrite oldest if full
        } else {
            ++currentSize;
        }

        prices[tail] = price;
        quantities[tail] = quantity;
        tail = (tail + 1) % maxSize;
    }

    bool isEmpty() const {
        return currentSize == 0;
    }

    bool isFull() const {
        return currentSize == maxSize;
    }

    MarketData getOldest() {
        if (isEmpty()) {
            throw std::out_of_range("Buffer is empty");
        }

        MarketData data;
        data.price = prices[head];
        data.quantity = quantities[head];

        head = (head + 1) % maxSize;
        --currentSize;
        return data;
    }
};

// AVL Tree with Preallocated Nodes for Cache Friendliness
class AVLTree {
private:
    struct Node {
        int price;
        int quantity;
        int leftIndex;
        int rightIndex;
        int height;

        Node() : price(0), quantity(0), leftIndex(-1), rightIndex(-1), height(1) {}
        Node(int p, int q) : price(p), quantity(q), leftIndex(-1), rightIndex(-1), height(1) {}
    };

    std::array<Node, AVL_TREE_MAX_NODES> nodes;  // Preallocated array of nodes
    int rootIndex;
    int nextAvailableIndex;

    int getHeight(int nodeIndex) const {
        return nodeIndex == -1 ? 0 : nodes[nodeIndex].height;
    }

    int getBalance(int nodeIndex) const {
        return nodeIndex == -1 ? 0 : getHeight(nodes[nodeIndex].leftIndex) - getHeight(nodes[nodeIndex].rightIndex);
    }

    int rightRotate(int yIndex) {
        int xIndex = nodes[yIndex].leftIndex;
        int T2Index = nodes[xIndex].rightIndex;

        // Perform rotation
        nodes[xIndex].rightIndex = yIndex;
        nodes[yIndex].leftIndex = T2Index;

        // Update heights
        nodes[yIndex].height = std::max(getHeight(nodes[yIndex].leftIndex), getHeight(nodes[yIndex].rightIndex)) + 1;
        nodes[xIndex].height = std::max(getHeight(nodes[xIndex].leftIndex), getHeight(nodes[xIndex].rightIndex)) + 1;

        return xIndex;
    }

    int leftRotate(int xIndex) {
        int yIndex = nodes[xIndex].rightIndex;
        int T2Index = nodes[yIndex].leftIndex;

        // Perform rotation
        nodes[yIndex].leftIndex = xIndex;
        nodes[xIndex].rightIndex = T2Index;

        // Update heights
        nodes[xIndex].height = std::max(getHeight(nodes[xIndex].leftIndex), getHeight(nodes[xIndex].rightIndex)) + 1;
        nodes[yIndex].height = std::max(getHeight(nodes[yIndex].leftIndex), getHeight(nodes[yIndex].rightIndex)) + 1;

        return yIndex;
    }

    int insertRecursive(int nodeIndex, int price, int quantity) {
        // 1. Perform the normal BST insertion
        if (nodeIndex == -1) {
            assert(nextAvailableIndex < AVL_TREE_MAX_NODES && "AVLTree has reached maximum node capacity.");
            nodes[nextAvailableIndex] = Node(price, quantity);
            return nextAvailableIndex++;
        }

        if (price < nodes[nodeIndex].price) {
            nodes[nodeIndex].leftIndex = insertRecursive(nodes[nodeIndex].leftIndex, price, quantity);
        }
        else if (price > nodes[nodeIndex].price) {
            nodes[nodeIndex].rightIndex = insertRecursive(nodes[nodeIndex].rightIndex, price, quantity);
        }
        else {
            // If the price already exists, update the quantity
            nodes[nodeIndex].quantity += quantity;
            return nodeIndex;
        }

        // 2. Update height of this ancestor node
        nodes[nodeIndex].height = 1 + std::max(getHeight(nodes[nodeIndex].leftIndex), getHeight(nodes[nodeIndex].rightIndex));

        // 3. Get the balance factor to check whether this node became unbalanced
        int balance = getBalance(nodeIndex);

        // 4. If the node is unbalanced, then try out the four cases

        // Left Left Case
        if (balance > 1 && price < nodes[nodes[nodeIndex].leftIndex].price)
            return rightRotate(nodeIndex);

        // Right Right Case
        if (balance < -1 && price > nodes[nodes[nodeIndex].rightIndex].price)
            return leftRotate(nodeIndex);

        // Left Right Case
        if (balance > 1 && price > nodes[nodes[nodeIndex].leftIndex].price) {
            nodes[nodeIndex].leftIndex = leftRotate(nodes[nodeIndex].leftIndex);
            return rightRotate(nodeIndex);
        }

        // Right Left Case
        if (balance < -1 && price < nodes[nodes[nodeIndex].rightIndex].price) {
            nodes[nodeIndex].rightIndex = rightRotate(nodes[nodeIndex].rightIndex);
            return leftRotate(nodeIndex);
        }

        // 5. Return the (unchanged) node pointer
        return nodeIndex;
    }

    void inOrderTraversal(int nodeIndex) const {
        if (nodeIndex != -1) {
            inOrderTraversal(nodes[nodeIndex].leftIndex);
            std::cout << "Price: " << nodes[nodeIndex].price << ", Quantity: " << nodes[nodeIndex].quantity << std::endl;
            inOrderTraversal(nodes[nodeIndex].rightIndex);
        }
    }

public:
    AVLTree() : rootIndex(-1), nextAvailableIndex(0) {}

    void insert(int price, int quantity) {
        rootIndex = insertRecursive(rootIndex, price, quantity);
    }

    void printInOrder() const {
        inOrderTraversal(rootIndex);
    }
};

int main() {
    RingBuffer ringBuffer;
    AVLTree bidTree;

    // Preallocated RingBuffer with size 5
    // Simulate receiving tick-by-tick data
    ringBuffer.insert(100, 20);
    ringBuffer.insert(101, 10);
    ringBuffer.insert(99, 15);
    ringBuffer.insert(102, 5);
    ringBuffer.insert(98, 25);

    // Simulate overwriting in RingBuffer
    ringBuffer.insert(103, 30);  // This will overwrite the oldest entry (100, 20)

    // Process ring buffer and insert data into AVL tree
    while (!ringBuffer.isEmpty()) {
        auto data = ringBuffer.getOldest();
        bidTree.insert(data.price, data.quantity);
    }

    // Print AVL tree contents (bids in sorted order)
    std::cout << "Bids in AVL Tree:" << std::endl;
    bidTree.printInOrder();

    return 0;
}
