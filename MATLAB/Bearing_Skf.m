function [Pvl,M_all,Mrr,Msl, Mdrag,Mseal]=Bearing_Skf(B,SchaftSpd,voil,Fa,Fr)
BearingType_name=B.BearingType;D=B.D;d=B.d;
SchaftSpd=abs(SchaftSpd);
Fa= abs(Fa);
Fr= abs(Fr);
miu_bl=0.015;miu_EHL=0.05;
R1=3.9e-7;R2=1.7;S1=3.23e-3;S2=36.5;Krs=3e-8;
Ks1=.0018;
Ks2=0;
dm=(D+d)/2;
type_bearing_name = ["RadialBallBearing", "TaperRollerBearing", ...
                    "NeedleRollerBearing", "CylindricalRollerBearing",...
                    "Thrust Pad", "ThrustNeedleRollerBearing",...
                    "Spline Rolling", "Sunk Key", "Kipphebellager"];
BearingType = find(type_bearing_name==BearingType_name);
switch BearingType
    %% Rillenkugellager
    case 1

        if SchaftSpd > 0
            C0=B.C0;
            Kz=3.1;
            H_bearing=B.H_bearing;
            % Rollreibungsmoment
            af=24.6.*(Fa./C0).^0.24;%Grad
            if  Fa == 0
                Grr =R1.*dm.^1.96.*Fr.^0.54;
            else
                Grr=R1.*dm.^1.96.*(Fr+R2./sind(af).*Fa).^0.54;%Rollreibungsgrundwert
            end
            eth_ish=(1+1.84e-9*voil^0.64.*(SchaftSpd.*dm).^1.28).^-1;%Schmierfilmdickenfaktor
            eth_rs=(exp(Krs.*voil.*SchaftSpd.*2.*dm.*sqrt(Kz./2./(D-d)))).^-1;
            Mrr  =eth_ish .*eth_rs.*Grr .*(SchaftSpd .*voil).^.6*10^-3;% N*m
            
            % Gleitreibungsmoment
            if nnz(Fa==0) ~= 0
                Gsl =S1.*dm.^-0.26.*Fr.^(5/3);%*******original is Gsl =S1.*dm.^-0.143.*Fr.^(5/3) ss104
            else
                Gsl =S1.*dm.^-0.145.*(Fr.^5+Fa.^4.*S2*dm.^1.5./sind(af)).^(1/3);%Gleitreibungsgrundwert
            end
            eth_bl=(exp(2.6e-8.*(SchaftSpd.*voil).^1.4.*dm)).^-1;
            miu_Sl=eth_bl.*miu_bl+(1-eth_bl).*miu_EHL;
            Msl=Gsl.*miu_Sl.*10^-3;
            
            %Berührungsdichtungen
            %         Mseal=(Ks1.*ds.^beta+Ks2)*1e-3;%*****original is Mseal=Ks1.*(D/1000).^beta+Ks2/1000 ss109 Einheit mm*N
            Mseal=0;
            %Strömungsverlust
            if H_bearing <= 0
                Mdrag=0;
            else
                H_d=[0 0.05 0.1 0.15 0.2 0.50 0.75 1 1.25 1.5];
                V_m=[0 0.00002 0.00007 0.00016 .00025 .00058 .00075 .00098 .00125 .00125];
                VM=interp1(H_d, V_m,H_bearing/dm,'pchip');%%ss112 diagram
                Kball=1e-12*Kz*(d+D)/(D-d);%S110                
                if H_bearing > dm % t OF RS calculation ss111
                    t_b=2.*acos((0.6*dm-dm)/(0.6*dm));
                elseif H_bearing>0
                    t_b=2.*acos((0.6*dm-H_bearing)/(0.6*dm));
                else
                    t_b=0;
                end
                %RS Calculation
                if t_b<=pi && t_b>=0
                    f_t=sin(0.5* t_b);
                elseif t_b<2*pi && t_b>pi
                    f_t=1;
                end
                f_A=0.05*Kz*(d+D)/(D-d);
                Rs=0.36*dm.^2*(t_b-sin(t_b))*f_A;
                Mdrag=(0.4*VM*Kball.*(dm).^5.*(SchaftSpd).^2+1.093e-7.*(SchaftSpd)^2.*(dm)^3.*(SchaftSpd.*(dm)^2.*f_t/voil).^(-1.379).*Rs)*10^-3;
                
                %             Mdrag=ones(x,1)* M_drag;
            end
            M_all=Mrr+Msl+Mdrag+Mseal;
            
            Pvl=(M_all).*SchaftSpd*2*pi/60;
        else
            Mrr=0;Msl=0; Mdrag=0;Mseal=0;Pvl=0;
        end
    case 2 %needle
        %         Krs=6e-8;
        %         Kz=6.2;
        if SchaftSpd==0 && Fr==0
            Mrr=0;Msl=0; Mdrag=0;Mseal=0;Pvl=0;
        else
            if Fr==0
                f0=12;
                if voil*SchaftSpd<2000
                    TVL0=160*10^(-10)*f0.*dm.^3;
                else
                    TVL0=10^(-10).*f0.*dm.^3.*(voil.*SchaftSpd).^(2/3);
                end
                T_1=0;
            else
                f0=12;
                if voil*SchaftSpd<2000
                    TVL0=160*10^(-10)*f0.*dm.^3;
                else
                    TVL0=10^(-10).*f0.*dm.^3.*(voil.*SchaftSpd).^(2/3);
                end
                f1=0.002;
                
                T_1=f1*Fr*dm*1e-3;
                %                 M_all=TVL0+T_1;
                
            end
            
%             Pvl=SchaftSpd*pi/30*(TVL0+T_1);
            Mrr=TVL0;
            Msl=T_1; Mdrag=0;Mseal=0;
        end
    case 3 %axial bearing

        f0=12;
        if SchaftSpd==0 && Fa==0
            Mrr=0;Msl=0; Mdrag=0;Mseal=0;Pvl=0;
        else
            if Fa==0
                if voil*SchaftSpd<2000
                    TVL0=160*10^(-10)*f0.*dm.^3;
                else
                    TVL0=10^(-10).*f0.*dm.^3.*(voil.*SchaftSpd).^(2/3);
                end
                T_1=0;
            else
                
                if voil*SchaftSpd<2000
                    TVL0=160*10^(-10)*f0.*dm.^3;
                else
                    TVL0=10^(-10).*f0.*dm.^3.*(voil.*SchaftSpd).^(2/3);
                end
                
                f1=0.0015;
                
                T_1=f1*Fa*dm*1e-3;
%                 M_all=TVL0+T_1;
            end
             Mrr=TVL0;
            Msl=T_1; Mdrag=0;Mseal=0;
        end
    case 4 %Kegelrollenlager

        if SchaftSpd > 0
            R1=B.R1 ;R2=B.R1 ;S1=B.S1 ;
            miu_bl=B.miu_bl ;miu_EHL=B.miu_EHL ;
            %Mrr
            Grr=R1*dm^2.38*(Fr+R2*B.Y*Fa)^0.31;
            eth_ish=(1+1.84e-9*voil^0.64.*(SchaftSpd.*dm).^1.28).^-1;%Schmierfilmdickenfaktor
            Krs=3e-8;Kz=5;Kl=0.7;
            eth_rs=(exp(Krs.*voil.*SchaftSpd.*2.*dm.*sqrt(Kz./2./(D-d)))).^-1;
            Mrr  =eth_ish .*eth_rs.*Grr .*(SchaftSpd .*voil).^.6*10^-3;
            %Msl
            Gsl=S1*dm^0.82*(Fr+B.S2*B.Y*Fa);
            eth_bl=(exp(2.6e-8.*(SchaftSpd.*voil).^1.4.*dm)).^-1;
            miu_Sl=eth_bl.*miu_bl+(1-eth_bl).*miu_EHL;
            Msl=Gsl.*miu_Sl.*10^-3;
            %Mdrag
            if H_bearing <= 0
                Mdrag=0;
            else
                H_d=[0 0.05 0.1 0.15 0.2 0.50 0.75 1 1.25 1.5];
                V_m=[0 0.00002 0.00007 0.00016 .00025 .00058 .00075 .00098 .00125 .00125];
                VM=interp1(H_d, V_m,H_bearing/dm,'pchip');%%ss112 diagram
                Kroll=1e-12*Kl* Kz*(d+D)/(D-d);%S110
                
                if H_bearing > dm % t OF RS calculation ss111
                    t_b=2.*acos((0.6*dm-dm)/(0.6*dm));
                elseif H_bearing>0
                    t_b=2.*acos((0.6*dm-H_bearing)/(0.6*dm));
                else
                    t_b=0;
                end
                %RS Calculation
                if t_b<=pi && t_b>=0
                    f_t=sin(0.5* t_b);
                elseif t_b<=2*pi && t_b>=pi
                    f_t=1;
                end
                f_A=0.05*Kz*(d+D)/(D-d);
                Rs=0.36*dm.^2*(t_b-sin(t_b))*f_A;
                Mdrag=0.4*VM*Kroll.*(dm).^5.*(SchaftSpd).^2+1.093e-7.*(SchaftSpd)^2.*(dm)^3.*(SchaftSpd.*(dm)^2.*f_t/voil).^(-1.379).*Rs;
                
                %             Mdrag=ones(x,1)* M_drag;
            end
            M_all=Mrr+Msl+Mdrag*1e-3;
            Mseal=0;
            Pvl=(M_all).*SchaftSpd*2*pi/60;
        else
            Mrr=0;Msl=0; Mdrag=0;Mseal=0;Pvl=0;
        end
    case 5

        %Zylinderrollenlager mit Kaefig
        R1=B.R1;S1=B.S1;S2=B.S2; Krs=3e-8;Kz=6.2;Kl=0.7;
        miu_bl=B.miu_bl;miu_EHL=B.miu_EHL;
        % Rollreibungsmoment berechnen
        Grr=R1.*dm.^2.41.*Fr.^0.31;
        eth_ish=(1+1.84e-9*voil^0.64.*(SchaftSpd.*dm).^1.28).^-1;   %Schmierfilmdickenfaktor
        eth_rs=(exp(Krs.*voil.*SchaftSpd.*2.*dm.*sqrt(Kz./2./(D-d)))).^-1;  %kinematische Schmierstoffverdrängungsfaktor
        %Krs    Beiwert für die Art der Schmierung
        %Kz     ein von der Lagerart abhängiger Designbeiwert
        Mrr=eth_ish .*eth_rs.*Grr .*(SchaftSpd .*voil).^0.6*10^-3 ;  %Rollreibungsmoment[Nmm]
        
        % Gleitreibungsmoment berechnen
        Gsl=S1.*dm.^0.9.*Fa+S2.*dm.*Fr;
        eth_bl=(exp(2.6e-8.*(SchaftSpd.*voil).^1.4.*dm)).^-1;
        miu_Sl=eth_bl.*miu_bl+(1-eth_bl).*miu_EHL;  %Gleitreibungszahl
        %eth_bl     Gewichtungsfaktor für die Gleitreibungszahl
        %miu_EHL    Reibungszahl eines ausreichend tragfähigen Schmierfilms
        Msl=Gsl.*miu_Sl*10^-3;   %Gleitreibungsmoment[Nmm]
        
        %Reinbungsmoment von Berührungsdichtungen
        Mseal=0;
        
        %Stömungsverlustabhängige Reibungsmoment
        % Ölstand H
        
        if H_bearing <= 0
            Mdrag=0;
        else
            Br=20;
            H_d=[0 0.05 0.1 0.15 0.2 0.50 0.75 1 1.25 1.5];
            V_m=[0 0.00004 0.00012 0.00023 .00036 .00070 .00098 .0012 .00146 .00146];
            VM=interp1(H_d, V_m,H_bearing/dm,'pchip');  %Ölbadwiderstandsvariable,Diagramm 4, Seite 112
            
            if H_bearing > dm % t OF RS calculation ss111
                t_b=2.*acos((0.6*dm-dm)/(0.6*dm));
            elseif H_bearing>0
                t_b=2.*acos((0.6*dm-H_bearing)/(0.6*dm));
            else
                t_b=0;
            end
            
            %RS Calculation
            if t_b<=pi && t_b>=0
                f_t=sin(0.5*t_b);
            elseif t_b<2*pi && t_b>pi
                f_t=1;
            end
            f_A=0.05*Kz*(d+D)/(D-d);
            RS=0.36*dm^2*(t_b-sin(t_b))*f_A;
            
            
            %Rollenlager
            I_D=5*Kl*Br/dm;
            %Br  Lagerbreite[mm]
            %Kl     ein von der Rollenlagerart abhängiger Designbeiwert
            Cw=2.789e-10*I_D^3-2.786e-4*I_D^2+0.0195*I_D+0.6439;
            Kroll=Kl*Kz*1e-12*(d+D)/(D-d);   %wälzkörperabhängiger Beiwert
            Mdrag=(4*VM*Kroll*Cw*Br*dm^4.*(SchaftSpd).^2+1.093e-7*(SchaftSpd).^2*dm.^3*((SchaftSpd*f_t*dm^2)/voil)^-1.379*RS)*10^-3;
            if SchaftSpd==0;Mdrag=0;end
        end
end
%%
M_all=Mrr+Msl+Mdrag+Mseal;
Pvl=(M_all).*SchaftSpd*2*pi/60;












