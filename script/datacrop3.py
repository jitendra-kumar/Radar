#!/usr/bin/env python3
# Crop raw data to create 12*6 30*30 matrices.
# Missing values are filled by mean values.
# radar_echo_classification, only 30, 40, 60 and 80 used
# Author: Yuping Lu <yupinglu89@gmail.com>
# Date: 02/16/2019

# load libs
import pyart
from scipy.stats import mode
import numpy as np
import numpy.ma as ma
import pandas as pd

cnt = {
    0 : 0, # Below Threshold (ND)
    10 : 0, # Biological (BI)
    20 : 0, # Anomalous Propagation/Group Clutter (GC)
    30 : 0, # Ice Crystals (IC)
    40 : 0, # Dry Snow (DS)
    50 : 0, # Wet Snow (WS)
    60 : 0, # Light and/or Moderate Rain (RA)
    70 : 0, # Heavy Rain (HR)
    80 : 0, # Big Drops (rain) (BD)
    90 : 0, # Graupel (GR)
    100 : 0, # Hail, possibly with rain (HA)
    120: 0,
    140 : 0, # Unknown Classification (UK)
    150 : 0 # Range Folded (RH)
}

idx = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
#idy = [0, 30, 60, 90, 120, 150]
idy = [150]

# Read data frames
df_n0c = pd.read_csv('/home/ylk/nexrad/name/n0c.txt', header = None)
df_n0h = pd.read_csv('/home/ylk/nexrad/name/n0h.txt', header = None)
df_n0k = pd.read_csv('/home/ylk/nexrad/name/n0k.txt', header = None)
df_n0r = pd.read_csv('/home/ylk/nexrad/name/n0r.txt', header = None)
df_n0x = pd.read_csv('/home/ylk/nexrad/name/n0x.txt', header = None)

f_error = open("name2/error.txt","w")
f_abandon = open("name2/abandon.txt","w")
f_label = open("name2/label.txt","w")
f_n0c = open("name2/n0c.txt","w")
f_n0k = open("name2/n0k.txt","w")
f_n0r = open("name2/n0r.txt","w")
f_n0x = open("name2/n0x.txt","w")

# Loop the files
for i in range(len(df_n0h.index)):
    #if i == 2:
    #    break
    # Read each variable file
    try:
        N0H = pyart.io.read('/home/ylk/nexrad/final/'+df_n0h.iloc[i,0])
    except:
        f_error.write('Error file: ' + df_n0h.iloc[i,0] + '\n')
        continue
        
    try:
        N0C = pyart.io.read('/home/ylk/nexrad/final/'+df_n0c.iloc[i,0])
    except:
        f_error.write('Error file: ' + df_n0c.iloc[i,0] + '\n')
        continue
        
    try:
        N0K = pyart.io.read('/home/ylk/nexrad/final/'+df_n0k.iloc[i,0])
    except:
        f_error.write('Error file: ' + df_n0k.iloc[i,0] + '\n')
        continue
        
    try:
        N0R = pyart.io.read('/home/ylk/nexrad/final/'+df_n0r.iloc[i,0])
    except:
        f_error.write('Error file: ' + df_n0r.iloc[i,0] + '\n')
        continue
        
    try:
        N0X = pyart.io.read('/home/ylk/nexrad/final/'+df_n0x.iloc[i,0])
    except:
        f_error.write('Error file: ' + df_n0x.iloc[i,0] + '\n')
        continue  
        
    # Check variable dims. If not match, stop and record the variable filename
    # error.txt
    data_n0h = N0H.fields['radar_echo_classification']['data']
    data_n0c = N0C.fields['cross_correlation_ratio']['data']
    data_n0k = N0K.fields['specific_differential_phase']['data']
    data_n0r = N0R.fields['reflectivity']['data']
    data_n0x = N0X.fields['differential_reflectivity']['data']
    
    if data_n0r.shape != (360, 230):
        f_error.write('Error dim: ' + df_n0r.iloc[i,0] + '\n')
        continue
    if data_n0h.shape != (360, 1200):
        f_error.write('Error dim: ' + df_n0h.iloc[i,0] + '\n')
        continue
    if data_n0c.shape != (360, 1200):
        f_error.write('Error dim: ' + df_n0c.iloc[i,0] + '\n')
        continue
    if data_n0k.shape != (360, 1200):
        f_error.write('Error dim: ' + df_n0k.iloc[i,0] + '\n')
        continue 
    if data_n0x.shape != (360, 1200):
        f_error.write('Error dim: ' + df_n0x.iloc[i,0] + '\n')
        continue
        
    # Extend n0r
    # Expand by 5 times
    data_n0r_repeat = np.repeat(data_n0r, 5, axis=1)
    # Insert another 1 every 23
    tres = np.empty((360, 0))
    for idk in range(1150):
        tres = np.append(tres, data_n0r_repeat[:,idk].reshape(360,1), axis=1)
        if (idk+1) % 23 == 0:
            tres = np.append(tres, data_n0r_repeat[:,idk].reshape(360,1), axis=1)
    if tres.shape != (360, 1200):
        f_error.write('Error dim: ' + df_n0r.iloc[i,0] + '\n')
        continue
    data_n0r = tres
    data_n0r = ma.masked_values(data_n0r, -999.0)
    
    # Crop the file into 72 30*30 matrices
    for j in range(len(idx)):
        for k in range(len(idy)):
            r1 = idx[j]
            c1 = idy[k]
            tmp_n0h = data_n0h[r1:r1+30, c1:c1+30]
            # mask 0, 10, 20, 50, 70, 90, 100, 120, 140, 150
            # If the valid values of n0h is less then 90, abadon that entry.
            # abadon.txt
            mx = ma.masked_values(tmp_n0h, 0.0) 
            mx = ma.masked_values(mx, 10.0) 
            mx = ma.masked_values(mx, 20.0)
            mx = ma.masked_values(mx, 50.0)
            mx = ma.masked_values(mx, 70.0)
            mx = ma.masked_values(mx, 90.0)
            mx = ma.masked_values(mx, 100.0)
            mx = ma.masked_values(mx, 120.0)
            mx = ma.masked_values(mx, 140.0) 
            mx = ma.masked_values(mx, 150.0) 
            t_n0h = mx.compressed()
            unmask_size = len(t_n0h)
            # unmask size >= 5%
            if unmask_size < 45:
                f_abandon.write('Too few n0h: ' + df_n0h.iloc[i,0] \
                                + ' ' + str(r1) + ' ' + str(c1) + '\n')
                continue
            # get the most frequent radar_echo_classification
            m = mode(t_n0h)
            mode_value = m[0][0]
            mode_count = m[1][0]
            #print(m)
            #print(mode_value)
            #print(mode_count)
            # mode count >= 2.5%
            if mode_count < 22:
                f_abandon.write('Mode Count is small: ' + df_n0h.iloc[i,0] \
                                + ' ' + str(r1) + ' ' + str(c1) + '\n')
                continue
            cnt[mode_value] += 1
            f_label.write(str(int(mode_value))+'\n')
            
            tmp_n0c = data_n0c[r1:r1+30, c1:c1+30]
            tmp_n0k = data_n0k[r1:r1+30, c1:c1+30]
            tmp_n0x = data_n0x[r1:r1+30, c1:c1+30]
            tmp_n0r = data_n0r[r1:r1+30, c1:c1+30]
            
            # Replace the missing values with mean values
            t_n0c = tmp_n0c.filled(tmp_n0c.mean())
            t_n0k = tmp_n0k.filled(tmp_n0k.mean())
            t_n0x = tmp_n0x.filled(tmp_n0x.mean())
            t_n0r = tmp_n0r.filled(tmp_n0r.mean())
            
            # Save the generate matrix with np
            n0c_name = 'n0c_' + str(i) + '_' + str(r1) + '_' + str(c1)
            n0k_name = 'n0k_' + str(i) + '_' + str(r1) + '_' + str(c1)
            n0x_name = 'n0x_' + str(i) + '_' + str(r1) + '_' + str(c1)
            n0r_name = 'n0r_' + str(i) + '_' + str(r1) + '_' + str(c1)
            
            np.savetxt('data2/' + n0c_name + '.csv', t_n0c, delimiter=",")
            np.savetxt('data2/' + n0k_name + '.csv', t_n0k, delimiter=",")
            np.savetxt('data2/' + n0x_name + '.csv', t_n0x, delimiter=",")
            np.savetxt('data2/' + n0r_name + '.csv', t_n0r, delimiter=",")
            
            f_n0c.write(n0c_name +'\n')
            f_n0k.write(n0k_name +'\n')
            f_n0x.write(n0x_name +'\n')
            f_n0r.write(n0r_name +'\n')
            
f_error.close()
f_abandon.close()
f_label.close() 
f_n0c.close() 
f_n0k.close()
f_n0x.close()
f_n0r.close()

for key, value in cnt.items():
    print(key, "=>", value)