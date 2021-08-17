import spidev
import time
import math
from gpiozero import LED

def init_spi(self):
	global spi, Q_time ,Q_Batt,Q_B_chg,kWh_dis,kWh_chg,cum_bp_kwh_in,\
	cum_bp_kwh_out,Q_B_dis,Q_nom,SOH ,R_shunt,Vt_ref,V_bat_Sum,Ai,Ai_offs,\
	Tj,Tbat,bal_stat,bal_stat2,p_genrun,p_charging ,p_loadshed,Fan_run_b, V_Cells,\
        Ah_b_max, Ah_b_min,T_Cells,err_no, Q_Cycles,bal_count,chg_out,load_out,Genrun,Fan_run


	# temp home for BMS constants
        err_no = 0
	Q_time = 0
	Q_Batt = 0.5*self.inst_capacity
	Q_B_chg = 0
	Q_Cycles = 0
        kWh_dis = 0
	kWh_chg = 0
	cum_bp_kwh_in=0
	cum_bp_kwh_out=0
	Q_B_dis = 0
	Q_nom = self.inst_capacity
	SOH = 1
	R_shunt = 0.025
        V_Cells = [0]*8
        T_Cells = [11]*8
	Vt_ref = 3.299
	V_bat_Sum = 25
	Ai = 0
	Ai_offs = 2.2
	Ah_b_max = 0
        Ah_b_min = 300
        Tj = 25
	Tbat = 25
	bal_stat = 0
	bal_stat2 = 0
        bal_count = [0]*8
        p_genrun  = False
	p_charging = True
	p_loadshed = False
	Fan_run_b = False

	chg_out = LED(2)
	load_out =LED(3)
	Genrun = LED(4)
	Fan_run = LED(17)

	spi = spidev.SpiDev()
	spi.open(0,0)
	spi.max_speed_hz = 500000
	spi.mode = 0
	return (spi)

def CrcA_MAX17( InputWord,WORD_LEN):
    CRC_LEN =3
    CRC_POLY =0x0B 
    CRC_SEED =0x000
    CRCMask =(CRC_POLY<<(WORD_LEN-1)) 
    LeftAlignedWord = InputWord<<CRC_LEN    # /* Clear the CRC bit in the data frame*/
    TestBitMask =  1 << ( WORD_LEN +2)
      
    BitCount = ( WORD_LEN )
    
    while (0 != BitCount):
        BitCount -=1
        if (0 != (LeftAlignedWord & TestBitMask)):   # is and
            LeftAlignedWord ^= CRCMask             # is xor
            
        CRCMask >>= 1
        TestBitMask >>= 1
   
    return (LeftAlignedWord)  #returns word with CRC apended; crc test.

def spi_xfer_MAX17(RW,Adr,xdata):
    global spi
    #*********************
    # Python 2.7 can't cope with 32 bit numbers
    #****************************
    txdata = [0,0,0,0]
    rxdata = [0,0,0,0]
    tdwd = RW<<8^Adr
    crca = CrcA_MAX17(tdwd,9)
    crcb = CrcA_MAX17(xdata,16)
    txword1 = 0^RW<<15
    txword2 = 0^RW<<3
    txword1 ^= Adr<<7
    txword1 ^= crca<<4
    txword1 ^= xdata&0xf000>>12
    txword2 ^= xdata&0xfff<<4
    txword2 ^= crcb
    txdata[0] =0^RW<<7^Adr>>1 #(txword1)>>8
    fadr = Adr&1
    gadr = fadr<<7
    txdata[1] =gadr^crca<<4^xdata>>12 #(txword1&0x00ff)
    txdata[2] =(xdata>>4)&0xff #(txword2)>>8
    txdata[3] =0^(xdata<<4)&0xff^RW<<3^crcb&0x7 #(txword2&0x00ff)
    
    rxdata = spi.xfer(txdata)  #
    
    flags = rxdata[0]
    crcs = flags&0x07
    flags = flags>>3
    if RW == 0:
        radr = rxdata[1]
        rdat = rxdata[2]<<8^rxdata[3]
        rcrc = 0
        rxok = rxdata[0]>>3&1 #crc check n-1
    else:
        radr = Adr
        rdat = 0^((rxdata[1]&0x0f)<<16^rxdata[2]<<8^rxdata[3])>>4
        rcrc = rxdata[3]&0x07
        rxok = (rxdata[3]>>3)&0x01
    
    
    time.sleep(.01)
    return(flags,crcs,radr,rdat,rcrc,rxok)

def init_max(self):
    #*************************************8
    # cell and battery parameters picked from get_settings()
    #********************************************8
    init_spi(self)
    time.sleep(0.1)
    for i in range(1,7):   
        spi_xfer_MAX17(0,i,0x00)        # clear por
    spi_xfer_MAX17(0,0x14,0x02)     # set spi int on AL out
    spi_xfer_MAX17(0,0x15,0x04)     #disable spi to
    spi_xfer_MAX17(0,0x16,0x00)     #enable gpio anlg in
    t_cell = self.cell_count+1
    tc = 0x2000
    tc = tc | t_cell<<8 |t_cell<<4 | t_cell
    spi_xfer_MAX17(0,0x18,tc)   # top cell selection
    spi_xfer_MAX17(0,0x19,0x3faf)   #IRQ enable
    ov = 0x4000
    for i in range(1,t_cell):
        ov |= 1<<i 
    spi_xfer_MAX17(0,0x1a,ov)   # Over voltage enable
    spi_xfer_MAX17(0,0x1b,ov)   # Under voltage enable
    spi_xfer_MAX17(0,0x1c,0xf)     # Aux Over voltage enable 0-5
    spi_xfer_MAX17(0,0x1d,0xf)     # Aux Under voltage enable 0-5
    ovc = int((self.V_C_max-0.1)/0.000305) # V_Cell max - 100mV
    spi_xfer_MAX17(0,0x1f,ovc<<2)   # over voltage clear thr 3.5V/.305mV <<2
    ovs = int((self.V_C_max)/0.000305) # V_Cell max
    spi_xfer_MAX17(0,0x20,ovs<<2)   # over voltage set thr 3.6V/.305mV <<2
    uvc = int((self.V_C_min+0.1)/0.000305) # V_Cell min - 100mV
    spi_xfer_MAX17(0,0x21,uvc<<2)   # under voltage clear thr 2.6V/.305mV <<2
    uvs = int((self.V_C_min)/0.000305) # V_Cell min 
    spi_xfer_MAX17(0,0x22,uvs<<2)   # under voltage set thr 2.5V/.305mV <<2
    spi_xfer_MAX17(0,0x23,0x514)    # cell mismatch set thr 0.1V/.305mV <<2
    bovc = int((self.max_battery_voltage-0.25)/0.003967) #max battery volt - 0.25
    spi_xfer_MAX17(0,0x28,bovc<<2)  # block ov clear thr 3.967mV <<2
    bovs = int((self.max_battery_voltage)/0.003967) #max battery volt 
    spi_xfer_MAX17(0,0x29,bovs<<2)  # block ov set thr 3.967mV <<2
    buvc = int((self.min_battery_voltage+0.25)/0.003967) #max battery volt + 0.25
    spi_xfer_MAX17(0,0x2a,buvc<<2)  # block uv cl thr 3.967mV <<2
    buvs = int((self.min_battery_voltage)/0.003967) #max battery volt 
    spi_xfer_MAX17(0,0x2b,buvs<<2)  # block uv set thr 0.9407/0.201mV <<2
    tovc = xtemp(self.T_C_min+5)    # Aux under temp clear T cell min + 5c - Neg temp coeff!!
    spi_xfer_MAX17(0,0x30,tovc<<2)   # Aux undertemp clear thr V/3.967mV <<2
    tovs = xtemp(self.T_C_min)    # Aux under temp set T cell min 
    spi_xfer_MAX17(0,0x31,tovs)   # Aux under temp set thr V/3.967mV <<2
    tuvc = xtemp(self.T_C_max-5)    # Aux over temp clear T cell max - 5c - Neg temp coeff!!
    spi_xfer_MAX17(0,0x32,tuvc<<2)   # Aux uv cl thr V/3.967mV <<2
    tuvs = xtemp(self.T_C_max)    # Aux over temp set T cell max  - Neg temp coeff!!
    spi_xfer_MAX17(0,0x33,tuvs<<2)   # Aux uv set thr 20.8V/3.967mV <<2
    spi_xfer_MAX17(0,0x5f,0x01)     # ADC Polarity
    spi_xfer_MAX17(0,0x62,0x4800)   # ADCQ CFG
    spi_xfer_MAX17(0,0x63,0x303)    # BALSWDLY 3 x 96uS
    cms =0x4000
    for i in range(0,t_cell):
        cms |= 1<<i
    spi_xfer_MAX17(0,0x64,cms)  # cell measure enable
    spi_xfer_MAX17(0,0x65,0x803F)   # filter init, AUX meas enable
    spi_xfer_MAX17(0,0x66,0xe21)    # configure and init scan
    spi_xfer_MAX17(0,0x80,0x00)         #reset Bal CTRL
    spi_xfer_MAX17(0,0x6f,0x1fe)
    spi_xfer_MAX17(0,0x7e,0x01)         #set bal uv thr = mincell
    spi_xfer_MAX17(0,0x6b,1)        # set die temp diag 1.
    return()

def xtemp(temp):
    t = temp+12.74
    s = math.exp(0.01988*t)
    r = int(0x3fff/s)
    return(r)

def vblk_dec(xdata,ref,adr):
    global V_bat_Sum,VBS_max,VBS_min,min_rst_en,Q_Batt
    vblock = xdata*ref
    #print(adr,"{:04x}".format(xdata),vblock)
    if adr == 22:
         V_bat_Sum = vblock
    
    return(vblock)

def stat_scan(self):
    for i in range(2,0x17): # Read Status
        f= spi_xfer_MAX17(1,i,0x0)
        if i == 2:
            st_wd1 = f[3]
        if i ==3:
            st_wd2 = f[3]
        if i == 5:
            fema1 = f[3]
    for i in range (2,7): #Write stat 1:3, Fema to clear
        f = spi_xfer_MAX17(0,i,0)
    
    en = err_dec(st_wd1,st_wd2,fema1,self)
    #print("stat",en)
    return(en)

def err_dec(st_wd1,st_wd2,fema1,self):
    global err_no, err_msg
    if st_wd1 & 0x04 > 0:
        err_no = 11
        err_msg = "Bal Error?"
    if st_wd1 & 0x8 > 0:
        err_no = 10
        err_msg = "Cal Error"
    if st_wd1 & 0x10 > 0 and st_wd2 & 0xd0 > 0:
        err_no = 9
        err_msg = "SPI Error"
    if st_wd1 & 0x80 > 0:
        err_no = 8
        err_msg = "Battery Over Temp"
        self.protection.temp_high_charge = True
    else:
        self.protection.temp_high_charge = False
    if st_wd1 & 0x100 > 0:
        err_no = 7
        err_msg = "Battery Under Temp"
        self.protection.temp_low_charge
    else:
        self.protection.temp_low_charge = False
    if st_wd1 & 0x200 > 0:
        err_no = 6
        err_msg = "Battery Undervoltage"
        self.protection.voltage_low = True
    else:
        self.protection.voltage_low = False
    if st_wd1 & 0x400 > 0:
        err_no = 5
        err_msg = "Battery Overvoltage"
        self.protection.voltage_high = True
    else:
        self.protection.voltage_high = False
    if st_wd1 & 0x800 > 0:
        err_no = 4
        err_msg = "Cell Undervoltage"
        self.protection.voltage_low_cell = True
    else:
        self.protection.voltage_low_cell = False
    if st_wd1 & 0x1000 > 0:
        err_no = 3 #overvoltage
        err_msg = "Cell Overvoltage"
        self.protection.voltage_high_cell = True
    else:
        self.protection.voltage_high_cell = False
    if st_wd1 & 0x2000 > 0:
        err_no = 2 #cell mismatch Dv too high
        err_msg = "Cell voltage mismatch"
        self.protection.cell_imbalance = True
    else:
        self.protection.cell_imbalance = False
    if st_wd1 & 0x4000 > 0:
        err_no = 1 #POR
        err_msg = "POR"
    if st_wd2 & 0x40 > 0:
        err_no = 13
        err_msg += " SPI CLK"
    if st_wd2 & 0x20 > 0:
        err_no = 14
        err_msg += " 16MHz CLK"
    if st_wd2 & 0x10 > 0:
        err_no = 15
        err_msg += " SPI INT BUS FLT"
    if fema1 &0x08 >0:
        err_no = 16
        #print(315)
        err_msg += " HV_UV"
    if fema1 &0x04 >0:
        err_no = 17
        #print(319)
        err_msg += " HV_DR"
    if fema1 &0x70 >0:
        err_no = 18
        err_msg += " gnd flt"
    if st_wd1 ==0 and st_wd2==0 and fema1 ==0:
        err_no = 0
        err_msg = "No Error"
        #store_reg([err_no],0)
    #print(328,err_no)
    return(err_no)   

def v_cell_d(self):
    global vc_del,vc_min,vc_max,Q_Batt, V_Cells,p_genrun,p_charging,p_loadshed
    vc_del = 0
    vc_max = 0
    vc_min = 4
    i_min =0
    i_max = 0
    b_lim = False
    
    for index,v in enumerate(V_Cells):
        
        if v > 3.55:
            b_lim = True
        if v> vc_max:
            vc_max = v
            i_max = index
        if v < vc_min:
            vc_min = v
            i_min = index
    
    self.cell_min_voltage = vc_min
    self.cell_max_voltage = vc_max  
    self.cell_min_no = i_min
    self.cell_max_no = i_max      

    vc_del = vc_max - vc_min
    # current control done elsewhere.
    if vc_min<(self.V_C_min+0.05) and vc_min > 0:
        p_genrun = True
        p_loadshed = True
        Q_Batt = 0
    elif vc_min > self.V_C_min+0.15:
        p_loadshed = False
    if vc_max > self.V_C_max-0.05:
        p_charging = False
        Q_Batt = Q_nom
    elif vc_max< self.V_C_max-0.15:
        p_charging = True
    inpins(self)    
    return(b_lim)  

def CSA(xdata,self):
    global R_shunt,Ai,Ai_offs
    Ai = (xdata*0.000305-2.5)/R_shunt +Ai_offs
    self.current = Ai
    calc_Ah(Ai,self)
    return(Ai)

def calc_Ah(Ai,self):
    global Q_Batt, Q_time,Q_B_chg,Q_B_dis,Ah_b_max,Ah_b_min,\
        x_soc_min,x_soc_max,x_Soc,Q_nom,SOH,kWh_chg,kWh_dis,V_bat_Sum,\
        cum_bp_kwh_in,cum_bp_kwh_out,p_genrun,Q_Cycles
    if Q_time == 0:
        Q_time = time.time()
    t_Q = time.time()
    d_Qt = t_Q-Q_time
    Q_time = t_Q

    dQ_Batt = Ai*d_Qt/3600
    Q_Batt +=dQ_Batt
    if Q_Batt > Q_nom:
        Q_Batt = Q_nom
    if Q_Batt < 0:
        Q_Batt = 0
    if Q_Batt > Ah_b_max:
        Ah_b_max = Q_Batt
    if Q_Batt < Ah_b_min:
        Ah_b_min = Q_Batt

    x_Soc = Q_Batt/Q_nom*100
    self.soc = x_Soc
    self.capacity_remain = x_Soc*Q_nom/100
    if x_Soc<20:
        p_genrun = True
    elif x_Soc > 35:
        p_genrun = False
        
    SOH = (1-cum_bp_kwh_out/Q_nom*0.00005)*100
    Q_act = Q_nom*SOH/100
    Q_Cycles = cum_bp_kwh_out/Q_nom*.00005 
    self.cycles = Q_Cycles
    # Need to convert SOH to cycles...
    # or add soh as dbus channel
    if Ai>0:
        Q_B_chg += dQ_Batt
        kWh_chg += dQ_Batt*V_bat_Sum/1000
        cum_bp_kwh_in +=dQ_Batt*V_bat_Sum/1000
    else:
        Q_B_dis -= dQ_Batt
        kWh_dis -= dQ_Batt*V_bat_Sum/1000
        cum_bp_kwh_out-= dQ_Batt*V_bat_Sum/1000
    
    return()

def gpio_decode(xdata,adr,self): 
    # need to add Dbus channel for device temp
    global Vt_ref,Tbat,T_Cells
    try:
        s = float(0x3fff)/float(xdata+1) 
        t = math.log(s)
        u = t/0.01998
        T_Cells[adr] = u-12.74
    except Exception as e:
        print("gpio_dec",e)
        print("gpio_dec",adr,"{:04x}".format(xdata))
        T_Cells[adr] = 25
    
    t_min = 100
    t_max = 0
    for i in range(0,4):
        if T_Cells[i] > t_max:
            t_max = T_Cells[i]
            imax = i 
        if T_Cells[i] < t_min:
            t_min = T_Cells[i]
            imin = i

    self.temp1 = (T_Cells[0]+T_Cells[1] )/2
    self.temp2 = (T_Cells[2]+T_Cells[3] )/2
    self.temp3 = (T_Cells[5]+T_Cells[6] )/2
    self.temp_max_no = imax
    self.temp_min_no = imin
    return()

def cell_balance(V_Cells,vc_min,vc_max,self):
    global bal_count,bal_stat,bal_stat2
    # need to add dbus channel for displaing balancing as 8 bit bianry?
    f = spi_xfer_MAX17(1,0x80,0x00)
    bal_stat = f[3]>>14
    if bal_stat ==3:
        spi_xfer_MAX17(0,0x80,0x0)
        spi_xfer_MAX17(0,0x6f,0x00)
        print("bal reset")
        return()
    if (bal_stat)&1 >0:
        #print("bal run")
        return() # Balancing in progress
    if (bal_stat) == 2: #balancing complete
        #print(511,"Bal Complete")
        for i in range (0x6f,0x81):
            spi_xfer_MAX17(0,i,0x00)
    else:
        f = spi_xfer_MAX17(0,0x80,0)
        if f[0] !=0:
            stat_clr()
        cb_sum = 0
        cb_duty = int((vc_max-vc_min-0.01)*500)
        if cb_duty >15:
            cb_duty  = 0xf
        max_cell = (f[3]>>8)&0x07
        min_cell = f[3]&0x07
        for i in range (1,9):
            Vc_t = int((V_Cells[i-1]-vc_min)/(vc_max-vc_min)*15)
            if Vc_t < 0:
                print(517,"<0")
                Vc_t = 0 # remove -ve 
            if Vc_t >=0 and V_Cells[i-1]>3.35:
                bal_count[i-1]+=Vc_t
                self.cells[i-1].balance = True
                if bal_count[i-1]>65535:
                    for j in range(0,8):
                        bal_count[j] = bal_count[j]>>1
            else:
                Vc_t = 0
                self.cells[i-1].balance = False
            cb_sum += Vc_t
            spi_xfer_MAX17(0,0x70+i,Vc_t) #set cell timers
            f = spi_xfer_MAX17(1,0x70+i,0) # and read back
            if f[3] != Vc_t:
                print(471,"Can't set T bal :",i)
                f = spi_xfer_MAX17(1,3,0)
                print("prt write rjt",f[3]&1)
        if cb_sum !=0:
            #enable cells & start timer
            f = spi_xfer_MAX17(0,0x6f,0x1fe) 
            if f[0] != 0:
                stat_clr()
            #R_bal_stat() Temporary for diagnostic
            xdata = 0x2002 | cb_duty<<4
            xdata = xdata%0xc7ff
            f = spi_xfer_MAX17(0,0x80,xdata)  
            #print(480,"{:04x}".format(f[3]),"{:02x}".format(f[0]))
            f = spi_xfer_MAX17(1,0x80,0)
            #print(481,"{:04x}".format(f[3]),"{:02x}".format(f[0]))
    return()    

def R_bal_stat():
    for i in range(0x6f,0x84):
        f = spi_xfer_MAX17(1,i,0x00)
        print("{:02x}".format(i),"{:04x}".format(f[3]),"{:02x}".format(f[0]))
    return()

def stat_clr():
    for i in range(2,7):
        spi_xfer_MAX17(0,i,0)
    return()

def die_temp(self):
    global Tj,tmaxp,Fan_run_b
    f= spi_xfer_MAX17(1,0x57,0) # read diag 1 register
    Vptat = f[3]>>2
    Vptat = Vptat/0x4000*2.3077
    Tj = Vptat/0.0032+8.3-273
    self.temp4 = Tj
    if Tj >45:
        Fan_run_b = True
    elif Tj < 40:
        Fan_run_b = False    
    
    return(Tj)

def inpins(self):
    global chg_in,Load_in,Genrun,Fan_run_b,chg_out,p_loadshed,p_charging,p_genrun
    if p_charging==True:
        self.charge_fet = True
        chg_out.on() 
    else:
        self.charge_fet = False 
        chg_out.off()

    if p_loadshed == False:
        self.discharge_fet = True
        load_out.on()
    else:
        self.discharge_fet = False
        load_out.off()
        p_gernun = True
    if p_genrun==True :
        Genrun.on()
    else:
        Genrun.off()
    if Fan_run_b == True:
        Fan_run.on()
    else:
        Fan_run.off()
    return()

def data_cycle(self):
    global err_no,T_Cells, vc_max
    #print("data_cycle")
    spi_xfer_MAX17(0,0x66,0xe21)
    f = spi_xfer_MAX17(1,0x66,0x00)
    scn_dn = f[3]>>15
    dat_rdy = (f[3]&0x2000)>>13
    while dat_rdy == 0 :
        f = spi_xfer_MAX17(1,0x66,0x00)
        time.sleep(0.005)
        scn_dn = (f[3]&0x8000)>>15
        dat_rdy = (f[3]&0x2000)>>13
            
    Tj = die_temp(self)
    f = spi_xfer_MAX17(1,0x66,0x00) # scan ctrl
    scn_dn = f[3]&0x8000>>15
    dat_rdy = f[3]&0x2000>>13
    spi_xfer_MAX17(0,0x83,0x1)# manual xfer
    f = spi_xfer_MAX17(0,0x66,0x1e28)
    if f[0]> 0:
        stat_clr()
    V_bat_sum = 0
    for i in range(72,0x50):
        f= spi_xfer_MAX17(1,i,0)
        v = vblk_dec((f[3]>>2),0.000305,i-72) #no change
        V_bat_sum += v
        V_Cells[i-72] = v
        cb_b = v_cell_d(self)
        time.sleep(0.005)
    self.voltage = V_bat_sum
    self.cells_v = V_Cells
    #print(V_Cells)
    if (vc_del >0.015 and Ai >1.0 and err_no <16 ) or cb_b == True or vc_max>3.45:
        self.poll_interval = 3000
        cell_balance(V_Cells,vc_min,vc_max,self)
    else:
        spi_xfer_MAX17(0,0x80,0x00)
        spi_xfer_MAX17(0,0x6f,0x00)
        self.poll_interval = 1000
    f= spi_xfer_MAX17(1,0x47,0)
    CSA(f[3]>>2,self)
    f= spi_xfer_MAX17(1,0x55,0)  # remeber to deduct V0 (AMPS) from V blk.
    vblk_dec((f[3]>>2),0.003967,22) 
    f= spi_xfer_MAX17(1,0x56,0)
    vblk_dec(f[3],0.00122,2) #02
    for i in range(0x59,0x5f,1):
        f= spi_xfer_MAX17(1,i,0)
        gpio_decode(f[3]>>2,i-89,self) #49-64
        time.sleep(0.005)
    stat_scan(self)
    return(True)

