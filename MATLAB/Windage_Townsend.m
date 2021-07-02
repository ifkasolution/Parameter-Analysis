function [PWL]=Windage_Townsend(gear,n)
df1=gear.da1;
m = gear.m;
b = gear.b;
n=abs(n);
P_wl_1=n^2.9*(0.16*(df1)^3.9+(df1)^2.9*b^0.75*m^1.15)*10e-20*1000*0.5;
% P_wl_2=(n/ratio)^2.9*(0.16*df2^3.9+df2^2.9*b^0.75*m^1.15)*10e-20*lemda*1000;
PWL=P_wl_1;
