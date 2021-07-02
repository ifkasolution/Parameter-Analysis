function [nu_ATF_org]=visko(t,nue1,nue2)
% t=t-2;
t1=40;                                    %Temperatur1 Einheit [°C]
% nue1=32;                                 %Viskosität1 Einheit [mm^2/s oder cSt]
t2=100;                                    %Temperatur2 EInheit [°C]
% nue2=6.4;                                %Viskosität2 Einheit [mm^2/s oder cSt]

m_vis=(log10(log10(nue2+0.7))-log10(log10(nue1+0.7)))/(log10(t1+273.15)-log10(t2+273.15));
k=m_vis*log10(t2+273.15)+log10(log10(nue2+0.7));
nu_ATF_org=10^(10^(k-m_vis*log10(t+273.15)))-0.7;
% % function rou_org=dichte(t_r)
% t1_r=15;                         %Temperatur1 Einheit [°C]
% rou_1=847;                       %Dichte des Schmierstoffs bei 15 °C [kg/m^3]
% t2_r=20;                         %Temperatur2 Einheit [°C]
% rou_2=842;                       %Dichte des Schmierstoffs bei 15 °C [kg/m^3]
% m_r=(rou_1-rou_2)/(t1_r-t2_r);
% n_r=rou_1-m_r*t1_r;
% rou_org=m_r*t+n_r;

