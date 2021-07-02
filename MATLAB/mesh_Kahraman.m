%%karahmann

function [Ps,T]=mesh_Kahraman(Gear,voil,Rho,n,T)
a=Gear.a;z1=Gear.z1;z2=Gear.z2;m=Gear.m;aw=Gear.aw;beta=Gear.beta;
da1=Gear.da1;da2=Gear.da2;b=Gear.b;ra=Gear.ra;miu=voil*Rho*1e3*10^-6;
n = abs(n); T = abs(T);
k=struct('k1',8.916465,'k2',1.03303 ,'k3',1.036077,'k4',0.354068,'k5',2.812084,'k6',0.100601,'k7',0.752755,'k8',0.390958,'k9',0.620305);
k1=k.k1;k2=k.k2;k3=k.k3;k4=k.k4;k5=k.k5;k6=k.k6;k7=k.k7;k8=k.k8;k9=k.k9;
% a=115;z1=31;z2=96;m=1.6;aw=17.5;beta=27;da1=60.2;da2=176.251;b=17;miu=6.4*843*10^-3;ra=2.5/6;v0=6.4;ra=2.5;
% 
% T=20;n=22000;
E=2.07e11;%pa
v_ratio=0.3;%poisson
if n==0
    Ps=0;T=0;
else
at=atan(tan(aw/360*2*pi)/cos(beta/360*2*pi));%transverse pressure Angle,a is normal pressure angle
y=a/m*cos(beta/360*2*pi)-(z1+z2)/2;%%T58:PDF central distance modification
awtt=acos((z1+z2)*cos(at)/(2*y+z1+z2));%transverse working pressure Angle

d1=m*z1/cos(beta/360*2*pi);
d2=m*z2/cos(beta/360*2*pi);
db1=z1*m*cos(at)/cos(beta/360*2*pi);
db2=z2*m*cos(at)/cos(beta/360*2*pi);
pet=m*pi*cos(at)/cos(beta/360*2*pi);
%%
s1=0.5*z1*(((da1/db1)^2-1)^0.5-tan(awtt))/pi;%divided by the basetoothpitch the length of mesh
s2=0.5*z2*(((da2/db2)^2-1)^0.5-tan(awtt))/pi;
s=(s1+s2);%überdeckung
sb=b*sind(beta)/m/pi;%sprungüberdeckung
% Lt=0.5*((da1^2-(d1*cos(aw/360*2*pi))^2)^0.5+(da2^2-(d2*cos(aw/360*2*pi))^2)^0.5-(db1+db2)*tan(aw/360*2*pi));
Xa=a*sin(awtt)/1000;
X1=Xa-(0.5*(da2^2-db2^2)^0.5)/1000;
X4=(0.5*(da1^2-db1^2)^0.5)/1000;
X3=X1+(pet)/1000;
X2=X4-(pet)/1000;
Xp=X1+(0.5*((da2^2-db2^2)^0.5-db2*tan(awtt)))/1000;%Wälzpunk
r=@(x) x.*(Xa-x)./(Xa);%equ of radiu
Vs=@(x) 0.1047*n*(1+(z2/z1))/(z2/z1)*abs(x-Xp);%sliding
Vt=@(x) n*2*pi/60*m*z1/cos(beta/360*2*pi)/2*(2*sin(aw/360*2*pi)-abs(x-Xp)/(0.5*d1)*(((z2/z1)+1)/(z2/z1)))/1000;
beta_b=atand(tand(beta)*cos(at));%Grundschrägungswinkel
lm=b/((4-s)/3*(1-sb)+sb/s);%Berührlinienlänge
%% %%%x1-x2 %%%%%%%%%%%%%%%%%%%%%%%%%%%
x1=X1:(X2-X1)/300:X2;
W1=T/(d1*cos(at)*cosd(beta_b))*1000;% Fn/2
r= x1.*(Xa-x1)./(Xa);%equ of radiu
Vs= 0.1047*n*(1+(z2/z1))/(z2/z1)*abs(x1-Xp);%sliding
Vt= n*2*pi/60*m*z1/cos(beta/360*2*pi)/2*(2*sin(aw/360*2*pi)-abs(x1-Xp)/(0.5*d1)*(((z2/z1)+1)/(z2/z1)))/1000;

P_h1= sqrt(W1/lm*1000./r./(pi*((1-v_ratio^2)/E*2)));
% P_h1=@(x) sqrt(W1/lm*1000./r(Xp).*1000/(pi*((1-v_ratio^2)/E*2)));
Ve=0.1047*n*Xa/2;
f_a1=-k1-k4*abs(2.*Vs./Vt).*P_h1*1e-9*log10(miu)+k5.*exp(-abs(2.*Vs./Vt).*P_h1*1e-9.*log10(miu))+k9*exp(ra);
fv1=exp(f_a1).*(P_h1*1e-9).^k2.*abs(2.*Vs./Vt).^k3*Ve^-k6*miu^k7.*r.^-k8;

Ps1=sum(2*W1*Vs.*fv1)*(X2-X1)/300;
%% %%%X3-x4%%%%%%%%%%%%%%%%%%%%%%%%%%%
x3=X3:(X4-X3)/300:X4;
W1=T/(d1*cos(at)*cosd(beta_b))*1000;% Fn/2
r= x3.*(Xa-x3)./(Xa);%equ of radiu
Vs= 0.1047*n*(1+(z2/z1))/(z2/z1)*abs(x3-Xp);%sliding
Vt= n*2*pi/60*m*z1/cos(beta/360*2*pi)/2*(2*sin(aw/360*2*pi)-abs(x3-Xp)/(0.5*d1)*(((z2/z1)+1)/(z2/z1)))/1000;

P_h1= sqrt(W1/lm*1000./r./(pi*((1-v_ratio^2)/E*2)));
% P_h1=@(x) sqrt(W1/lm*1000./r(Xp).*1000/(pi*((1-v_ratio^2)/E*2)));
Ve=0.1047*n*Xa/2;
f_a1=-k1-k4*abs(2.*Vs./Vt).*P_h1*1e-9*log10(miu)+k5.*exp(-abs(2.*Vs./Vt).*P_h1*1e-9.*log10(miu))+k9*exp(ra);
fv1=exp(f_a1).*(P_h1*1e-9).^k2.*abs(2.*Vs./Vt).^k3*Ve^-k6*miu^k7.*r.^-k8;



Ps3=sum(2*W1*Vs.*fv1)*(X4-X3)/300;

%% %%%x2-x3 %%%%%%%%%%%%%%%%%%%%%%%%%
x2=X2:(X3-X2)/300:X3;
r=x2.*(Xa-x2)./(Xa);%equ of radiu
Vs= 0.1047*n*(1+(z2/z1))/(z2/z1)*abs(x3-Xp);%sliding
Vt=n*2*pi/60*m*z1/cos(beta/360*2*pi)/2*(2*sin(aw/360*2*pi)-abs(x3-Xp)./(0.5*d1)*(((z2/z1)+1)/(z2/z1)))/1000;

W2=T/(d1*cos(at)*cosd(beta_b))*2000;
P_h2=sqrt(W2/lm*1000./r./(pi*((1-v_ratio^2)/E*2)));
% P_h2=@(x) sqrt(W1/lm*1000./r(Xp).*1000/(pi*((1-v_ratio^2)/E*2)));
f_a2= -k1-k4*abs(2.*Vs./Vt).*P_h2*1e-9*log10(miu)+k5.*exp(-abs(2.*Vs./Vt).*P_h2*1e-9.*log10(miu))+k9*exp(ra);
fv2= exp(f_a2).*(P_h2*1e-9).^k2.*abs(2.*Vs./Vt).^k3*Ve^-k6*miu^k7.*r.^-k8;
Ps2=sum( W2*Vs.*fv2)*(X3-X2)/300;
%% %%
Ps=(Ps1+Ps2+Ps3)/(X4-X1);
T=Ps/(n*pi/30)*z2/z1;
end
% x2=X2:(X3-X2)/100:X3;
% x1=X1:(X2-X1)/100:X2;
% x3=X3:(X4-X3)/100:X4;
% f_all=[fv1(x1) fv2(x2) fv1(x3)];
% P_all=[2*W1*Vs(x1).*fv1(x1) W2.*Vs(x2).*fv2(x2) 2*W1*Vs(x3).*fv1(x3)];

%% %%%%%%
% figure (2);
% plot(x1,2*W1*Vs(x1).*fv1(x1),'Color','Red','LineWidth',2);
% hold on;
% plot(x2,W2*Vs(x2).*fv2(x2),'Color','Red','LineWidth',2);
% plot(x3,2*W1*Vs(x3).*fv1(x3),'Color','Red','LineWidth',2);
%
% ylabel('Sliding Power Loss (W)','FontSize',15,'FontName','Arial');
% xlabel('Contact Path(m)','FontSize',15,'FontName','Arial');
% figure (4)
% plot(x1,fv1(x1),'Color','Red','LineWidth',2);hold on;
% plot(x2,fv2(x2),'Color','Red','LineWidth',2);
% plot(x3,fv1(x3),'Color','Red','LineWidth',2);
%% %%%%%%%%%
% P_h1=0.5;ra=0.2;r=0.02;Ve=15;miu=5.2;R=0.04;
% % P_h1=@(x) sqrt(W1/lm*1000./r(Xp).*1000/(pi*((1-v_ratio^2)/E*2)));
% SR=0:0.1:1;
% f_a1=-b1-b4*SR.*P_h1*log10(miu)+b5.*exp(-SR.*P_h1.*log10(miu))+b9*exp(ra);
% fv=exp(f_a1).*(P_h1).^b2.*SR.^b3*Ve^-b6*miu^b7.*R.^-b8;
% plot(SR,fv);ylim([0 0.03])

