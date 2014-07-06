#include "sub.h"
namespace sub {
    int a;
    array<int, 2> b;
    array<array<int, 2>, 2> c;
    _type_a_ d;
    array<_type_a_, 2> e;
    array<int, 2> _var_a_;
    int f;
    int g;
    _type_b_ _var_b_;
    array<int, 2> h;
    int i;
    _type_b_ _var_c_;
    array<int, 2> _var_d_;
    int j;
    int k;
    int m;
    _type_e_ n;

    int main(std::string __name__) {
        a = 1;
        b = (array<int, 2>){2, 3};
        c = (array<array<int, 2>, 2>){ 4, 5 ,  6, 7 };
        d = (_type_a_){8,  9, 10 };
        e = (array<_type_a_, 2>){d, d};
        _var_a_ = (array<int, 2>){1, 2};
        f = _var_a_[0];
        g = _var_a_[1];
        _var_b_ = (_type_b_){ 3, 4 , 5};
        h = _var_b_._0;
        i = _var_b_._1;
        _var_c_ = (_type_b_){h, i};
        _var_d_ = _var_c_._0;
        j = _var_d_[0];
        k = _var_d_[1];
        m = _var_c_._1;
        n = (_type_e_){1,   2, 3 , 4 ,    5 , 6,  7, 8  ,  9, 10  };

        return 0;
    }
}