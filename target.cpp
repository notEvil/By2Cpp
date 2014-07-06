#include "target.h"
namespace target {
    array<int, 2> _var_a_;
    std::vector<int> b;
    array<array<int, 2>, 2> _var_b_;
    std::vector<array<int, 2> > c;
    array<int, 2> _var_c_;
    _type_a_ d;
    array<_type_a_, 2> _var_d_;
    std::vector<_type_a_> e;
    array<int, 2> _var_e_;
    std::vector<int> _var_f_;
    int f;
    int g;
    array<int, 2> _var_g_;
    _type_b_ _var_h_;
    std::vector<int> h;
    int i;
    _type_b_ _var_i_;
    std::vector<int> _var_j_;
    int j;
    int k;
    int m;
    int fun(int x) {
        int _default_a_ = _inner_fun_y_;
        _inner_fun_y_ = x;
        int r = inner_fun(_inner_fun_y_);
        int _return_b_ = r;
        _inner_fun_y_ = _default_a_;
        return _return_b_;
    }
    int _inner_fun_y_;
    int inner_fun(int y) {
        int _return_a_ = y;

        return _return_a_;
    }
    int main(std::string __name__) {
        sub::main("sub");
        #define sub SUB
        sub2::main("sub2");
        _var_a_ = (array<int, 2>){2, 3};
        b = std::vector<int>(_var_a_.begin(), _var_a_.end());
        _var_b_ = (array<array<int, 2>, 2>){ 4, 5 ,  6, 7 };
        c = std::vector<array<int, 2> >(_var_b_.begin(), _var_b_.end());
        _var_c_ = (array<int, 2>){9, 10};
        d = (_type_a_){8, std::vector<int>(_var_c_.begin(), _var_c_.end())};
        _var_d_ = (array<_type_a_, 2>){d, d};
        e = std::vector<_type_a_>(_var_d_.begin(), _var_d_.end());
        _var_e_ = (array<int, 2>){1, 2};
        _var_f_ = std::vector<int>(_var_e_.begin(), _var_e_.end());
        f = _var_f_[0];
        g = _var_f_[1];
        _var_g_ = (array<int, 2>){3, 4};
        _var_h_ = (_type_b_){std::vector<int>(_var_g_.begin(), _var_g_.end()), 5};
        h = _var_h_._0;
        i = _var_h_._1;
        _var_i_ = (_type_b_){h, i};
        _var_j_ = _var_i_._0;
        j = _var_j_[0];
        k = _var_j_[1];
        m = _var_i_._1;
        fun(0);
        #undef SUB

        return 0;
    }
}
int main(int argc, char const* argv[]) {
    return target::main("__main__");
}