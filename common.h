#pragma once
#include <string>
#include <vector>

template<typename T, int size>
struct array {
    T _data[size];

    T& operator[](int const& index) {
	return _data[index];
    }

    T* operator+(int value) {
	return _data + value;
    }

    T* begin() {
	return _data;
    }

    T* end() {
	return _data + size;
    }
};

