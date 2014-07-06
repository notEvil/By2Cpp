#pragma once
#include "common.h"
#include "target.hidden"
#include "sub.h"
#include "sub2.h"
namespace target {
    int main(std::string __name__);
    extern array<int, 2> _var_a_;
    extern std::vector<int> b;
    extern array<array<int, 2>, 2> _var_b_;
    extern std::vector<array<int, 2> > c;
    extern array<int, 2> _var_c_;
    extern _type_a_ d;
    extern array<_type_a_, 2> _var_d_;
    extern std::vector<_type_a_> e;
    extern array<int, 2> _var_e_;
    extern std::vector<int> _var_f_;
    extern int f;
    extern int g;
    extern array<int, 2> _var_g_;
    extern _type_b_ _var_h_;
    extern std::vector<int> h;
    extern int i;
    extern _type_b_ _var_i_;
    extern std::vector<int> _var_j_;
    extern int j;
    extern int k;
    extern int m;
    int fun(int x);
    extern int _inner_fun_y_;
    int inner_fun(int y);
}