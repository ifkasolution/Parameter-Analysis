function [Pvl,Tp,Cm_1,Cm_2,Cm_3,Cm_4]=Blank_Changenet(Gear,voil,Rho,Vol,n)
z1=Gear.z1;m=Gear.m;aw=Gear.aw;b1=Gear.b;beta=Gear.beta;
da1=Gear.da1;df1=Gear.df1;he1=Gear.he1;
n=abs(n);
x(1:6)=[ 1.366              0.45           0.1             0.21           0.6                      0.21];
%             7                8                9              10             11                       12
%          Cm2_1              Cm2_2          Cm2_3           Cm2_4          Cm2_5                    Cm2_6
x(7:12)=[ 0.239              0.45           0.1             1e-8           0.6                      0.21 ];
%             13               14               15            16              17                       18
%          Cm3_1              Cm3_2          Cm3_3           Cm3_4          Cm3_5                    Cm3_6
x(13:18)=[ 20.797              0.1           0.35             0.21           0.88                     0.85   ];
%            19               20               21            22              23                       24
%          Cm4_1              Cm4_2          Cm4_3           Cm4_4          Cm4_5                    Cm4_6
x(19:24)=[ 3.644              0.1            0.35             1e-8           0.88                     0.85   ];
CM=struct('Cm1_1',x(1),'Cm1_2',x(2),'Cm1_3',x(3),'Cm1_4',x(4),'Cm1_5',x(5),'Cm1_6',x(6),...
          'Cm2_1',x(7),'Cm2_2',x(8),'Cm2_3',x(9),'Cm2_4',x(10),'Cm2_5',x(11),'Cm2_6',x(12),...
           'Cm3_1',x(13),'Cm3_2',x(14),'Cm3_3',x(15),'Cm3_4',x(16),'Cm3_5',x(17),'Cm3_6',x(18),...
        'Cm4_1',x(19),'Cm4_2',x(20),'Cm4_3',x(21),'Cm4_4',x(22),'Cm4_5',x(23),'Cm4_6',x(24));
Cm1_1=CM.Cm1_1;Cm1_2=CM.Cm1_2;Cm1_3=CM.Cm1_3;Cm1_4=CM.Cm1_4;Cm1_5=CM.Cm1_5;Cm1_6=CM.Cm1_6;
Cm2_1=CM.Cm2_1;Cm2_2=CM.Cm2_2;Cm2_3=CM.Cm2_3;Cm2_4=CM.Cm2_4;Cm2_5=CM.Cm2_5;Cm2_6=CM.Cm2_6;
Cm3_1=CM.Cm3_1;Cm3_2=CM.Cm3_2;Cm3_3=CM.Cm3_3;Cm3_4=CM.Cm3_4;Cm3_5=CM.Cm3_5;Cm3_6=CM.Cm3_6;
Cm4_1=CM.Cm4_1;Cm4_2=CM.Cm4_2;Cm4_3=CM.Cm4_3;Cm4_4=CM.Cm4_4;Cm4_5=CM.Cm4_5;Cm4_6=CM.Cm4_6;
% Gear.GearCon=struct('a',69, 'z1',29,'z2',39,'m',1.8,'aw',17.5,'beta',31,'da1',66.85,'da2',87.85,'df1',55.25,'df2',76.35,'b1',23.8,'b2',21,'ra',0.8,'he1',0,'he2',44.95);
% n=6000;
% Rho=842;voil=6.4;Vol=0.0013;
% z1=Gear.GearCon.z1;z2=Gear.GearCon.z2;m=Gear.GearCon.m;aw=Gear.GearCon.aw;b1=Gear.GearCon.b1;b2=Gear.GearCon.b2;beta=Gear.GearCon.beta;
% da1=Gear.GearCon.da1;da2=Gear.GearCon.da2;df1=Gear.GearCon.df1;df2=Gear.GearCon.df2;he1=Gear.GearCon.he1;he2=Gear.GearCon.he2;

%% gear 1
d1=m*z1/cos(beta/360*2*pi); 
v1=n./60*2*pi;
Re=v1.*d1/2000*b1/1000*1e6/voil;
Fr1=v1.^2*d1/2000/9.8;
Upsilon=v1.^2*(d1/2000*b1/1000*m/1000)^(1/3);
Rec=4000;
Identi.v1=750;Identi.v2=1250;
if he1<=0 ||n==0
    Tpl1=0;
    Pvl1=0;
else
    %     c4000=1.366*(he1/d1)^0.45*(Vol/d1^3*1e9)^0.1.*Re.^-0.21.*Fr1.^-0.6;
    %     c9000=3.644*(b/d1)^0.85*0.1*(Vol/d1^3*1e9)^-0.35*Fr1.^-0.88;
    Cm_1=Cm1_1*(he1/d1)^Cm1_2*(Vol/d1^3*1e9)^Cm1_3.*Re.^-Cm1_4.*Fr1.^-Cm1_5*(b1/d1)^Cm1_6;
    Cm_2=Cm2_1*(he1/d1)^Cm2_2*(Vol/d1^3*1e9)^Cm2_3.*Fr1.^-Cm2_5*(b1/d1)^Cm2_6;
    Cm_3=Cm3_1*(he1/d1)^Cm3_2*(Vol/d1^3*1e9)^-Cm3_3.*Re.^-Cm3_4.*Fr1.^-Cm3_5*(b1/d1)^Cm3_6;
    Cm_4=Cm4_1*(he1/d1)^Cm4_2*(Vol/d1^3*1e9)^-Cm4_3.*Fr1.^-Cm4_5*(b1/d1)^Cm4_6;
    if Re < Rec && Upsilon < Identi.v1
        Cm1 =Cm_1;
        
    elseif  Re > Rec && Upsilon < Identi.v1
        Cm1 =Cm_2;
        
    elseif Re < Rec && Upsilon > Identi.v2
        Cm1 =Cm_3;
        
    elseif Re > Rec && Upsilon > Identi.v2
        Cm1 =Cm_4;
    else
        if Re > Rec
            Cm1=(Cm_4-Cm_2)./(Identi.v2-Identi.v1).*(Upsilon-Identi.v1)+Cm_2;
        else
            Cm1=(Cm_3-Cm_1)./(Identi.v2-Identi.v1).*(Upsilon-Identi.v1)+Cm_1;
        end
            
    end
    if he1> d1
        he1=d1;
    end
    Theta=acos(1-he1/d1*2);%R
    Sl1=(d1/2000)^2*(2*Theta-sin(2*Theta));
    h_tooth_1=(da1-df1)/2000;
    St1=d1/2000*b1/1000*Theta+2*z1*Theta*h_tooth_1*b1/1000/(pi*cos(aw/360*2*pi)*cos(beta/360*2*pi));
    Sm1=Sl1+St1;
    Tpl1=0.5*Rho.*(d1/2000)^3.*Sm1.*Cm1.*v1.^2;
    Pvl1=0.5*Rho.*(d1/2000)^3.*Sm1.*Cm1.*v1.^3;
end
%% sum
Pvl=Pvl1;
Tp=Tpl1;