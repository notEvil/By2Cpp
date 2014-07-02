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


/* -- hidden -- */
struct _type_a_ {
    int _0;
    array<int, 2> _1;
};
struct _type_b_ {
    array<int, 2> _0;
    int _1;
};
struct _type_c_ {
    array<int, 1> _0;
    int _1;
    array<int, 2> _2;
};
struct _type_d_ {
    _type_c_ _0;
    array<int, 2> _1;
};
struct _type_e_ {
    int _0;
    _type_b_ _1;
    _type_d_ _2;
};
struct _type_f_ {
    int _0;
    std::vector<int> _1;
};
struct _type_g_ {
    std::vector<int> _0;
    int _1;
};
/* -- hidden -- */

int main(int argc, const char* argv[]) {
    int a = 1;
    array<int, 2> b = {2, 3};
    array<array<int, 2>, 2> c = { 4, 5 ,  6, 7 };
    _type_a_ d = {8,  9, 10 };
    array<_type_a_, 2> e = {d, d};
    array<int, 2> _var_a_ = {1, 2};
    int f = _var_a_[0];
    int g = _var_a_[1];
    _type_b_ _var_b_ = { 3, 4 , 5};
    array<int, 2> h = _var_b_._0;
    int i = _var_b_._1;
    _type_b_ _var_c_ = {h, i};
    array<int, 2> _var_d_ = _var_c_._0;
    int j = _var_d_[0];
    int k = _var_d_[1];
    int m = _var_c_._1;
    _type_e_ n = {1,   2, 3 , 4 ,    5 , 6,  7, 8  ,  9, 10  };
    array<int, 2> _var_e_ = {2, 3};
    std::vector<int> B = std::vector<int>(_var_e_.begin(), _var_e_.end());
    array<array<int, 2>, 2> _var_f_ = { 4, 5 ,  6, 7 };
    std::vector<array<int, 2> > C = std::vector<array<int, 2> >(_var_f_.begin(), _var_f_.end());
    array<int, 2> _var_g_ = {9, 10};
    _type_f_ D = {8, std::vector<int>(_var_g_.begin(), _var_g_.end())};
    array<_type_f_, 2> _var_h_ = {D, D};
    std::vector<_type_f_> E = std::vector<_type_f_>(_var_h_.begin(), _var_h_.end());
    array<int, 2> _var_i_ = {1, 2};
    std::vector<int> _var_j_ = std::vector<int>(_var_i_.begin(), _var_i_.end());
    int F = _var_j_[0];
    int G = _var_j_[1];
    array<int, 2> _var_k_ = {3, 4};
    _type_g_ _var_l_ = {std::vector<int>(_var_k_.begin(), _var_k_.end()), 5};
    std::vector<int> H = _var_l_._0;
    int I = _var_l_._1;
    _type_g_ _var_m_ = {H, I};
    std::vector<int> _var_n_ = _var_m_._0;
    int J = _var_n_[0];
    int K = _var_n_[1];
    int M = _var_m_._1;
}



