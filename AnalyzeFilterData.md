```python
import pandas as pd
import matplotlib.pyplot as plt
from datetime import *
import numpy as np
#import peakutils
```

# Data Munging

```python
#bring in the summary table 
#format the date time inorder to merge with data files
summary_df = pd.read_csv("Data/3MTestingLog.csv")
summary_df = summary_df.drop(['Table Name'], axis=1)
summary_df["Install Date Time"] = pd.to_datetime(summary_df['Date'] + ' ' + summary_df['Install Time'], format="%m/%d/%y %H:%M")
summary_df["Removal Date Time"] = pd.to_datetime(summary_df['Date'] + ' ' + summary_df['Removal Time'], format="%m/%d/%y %H:%M")

#fix the dates for when the sample was removed the following day after installation.
for i in range(len(summary_df['Date'])):
    if summary_df['Removal Date Time'][i] < summary_df['Install Date Time'][i]:
        summary_df['Removal Date Time'][i] = summary_df['Removal Date Time'][i] + timedelta(days=1)


#Bring in the testing data 
#Had to seperate the files because some of them had different headers for the filter pressure drop
datafiles1 = ["Data/Data-20191120134426.csv", "Data/Data-20191121080221_0.csv", "Data/Data-20191121080221_1.csv"]

datafiles2 = ["Data/Data-20191122074415.csv", "Data/Data-20191125071926_0.csv", "Data/Data-20191125071926_1.csv", 
             "Data/Data-20191126061705_0.csv", "Data/Data-20191126061705_1.csv", "Data/Data-20191127053638.csv"]

usecols1 = ['Date', 'Time', "Volts", 'Volts.1', 'Amps', 'Amps.1', 'Volts.2', 'Volts.3', 'Amps.2', 'Amps.3', '0']

usecols2 = ['Date', 'Time', "Volts", 'Volts.1', 'Amps', 'Amps.1', 'Volts.2', 'Volts.3', 'Amps.2', 'Amps.3', 'In. H2']


#pullin the first file as a dataframe, pull the desired columns and drop the first row since there are two header rows
AllData_df = pd.DataFrame()

for file1 in datafiles1: 
    Data1_df = pd.read_csv(file1, skiprows=1, usecols=usecols1) 
    
    NonZeroData1_df = Data1_df.loc[(Data1_df['Volts']!=0)]

    AllData_df = AllData_df.append(NonZeroData1_df, ignore_index=True)
    
#remove all of the rows with zeros
#AllData_df = Data1_df.loc[(Data1_df['Volts']!=0)]

#rename the filter pressure drop column to match the rest of the files
AllData_df = AllData_df.rename(columns={'0': 'In. H2'})


#pull in all of the other data files and create one large file while removing all zero values
for file in datafiles2:
    Data2_df = pd.read_csv(file, skiprows=1, usecols=usecols2)

    NonZeroData2_df = Data2_df.loc[(Data2_df['Volts']!=0)]
        
    AllData_df = AllData_df.append(NonZeroData2_df, ignore_index=True)
    

AllData_df = AllData_df.rename(columns={'In. H2': 'Filter Pressure Drop (in/H2O)'})
    
AllData_df['Date and Time'] = pd.to_datetime(AllData_df['Date'] + ' ' + AllData_df['Time'], format="%Y/%m/%d %H:%M:%S")

ZeroData_df = AllData_df.loc[AllData_df['Volts'] == 0]


#calculating Watts column as Volts+Volts.1 * Amps+Amps.1

CalculatedColumns_df = AllData_df.copy()
CalculatedColumns_df['Whole Home Power (kW)'] = ((CalculatedColumns_df['Volts']+CalculatedColumns_df['Volts.1']) * (CalculatedColumns_df['Amps']+CalculatedColumns_df['Amps.1']))/1000
CalculatedColumns_df['Compressor Power (kW)'] = ((CalculatedColumns_df['Volts.2']+CalculatedColumns_df['Volts.3']) * CalculatedColumns_df['Amps.2'])/1000
CalculatedColumns_df['Blower Fan Power (kW)'] = (CalculatedColumns_df['Amps.3'])*120/1000
CalculatedColumns_df['Compressor and Fan Power (kW)'] = CalculatedColumns_df['Compressor Power (kW)'] + CalculatedColumns_df['Blower Fan Power (kW)']
CalculatedColumns_df


#create new columns in AllData_df by using conditional (mask) and data from summary_df
#with using the combined column date and time

for i in range(len(summary_df['Filter ID'])):
    mask = (CalculatedColumns_df['Date and Time'] >= summary_df['Install Date Time'][i]) & (CalculatedColumns_df['Date and Time'] <= summary_df['Removal Date Time'][i])

    #based on the summary table, what was the filter ID during this time fame
    CalculatedColumns_df.loc[mask, 'Filter ID'] = summary_df['Filter ID'][i]
    
    #based on the summary table was the outside of the home during heating or cooling season during this time fame
    CalculatedColumns_df.loc[mask, 'Outdoor Temp'] = summary_df['Outdoor Temp'][i]
    
    #based on the summary table is the filter dirty or clean during this time fame
    if (summary_df['Filter ID'][i]=='MERV 8-4') | (summary_df['Filter ID'][i]=='MERV 8-5') | (summary_df['Filter ID'][i]=='MERV 13-4') | (summary_df['Filter ID'][i]=='MERV 13-5'):
        CalculatedColumns_df.loc[mask, 'Clean/Dirty'] = 'Dirty'
    else:
        CalculatedColumns_df.loc[mask, 'Clean/Dirty'] = 'Clean'
        
    #added a rolling count of seconds the filter was tested for during this time fame
    CalculatedColumns_df.loc[mask, 'Cumulative Time in Test (sec)'] = CalculatedColumns_df.loc[mask, 'Filter ID'].rolling(len(CalculatedColumns_df.loc[mask, 'Filter ID'])).count()

#remove the na's. This will be the time between the tests
FilteredData_df = CalculatedColumns_df.dropna()


second_cut_off = 7200

FilterID_CleanDirty_Combined_df = FilteredData_df.copy()
FilterID_CleanDirty_Combined_df['Filter ID'] = FilterID_CleanDirty_Combined_df['Filter ID'] + str(' ') + FilterID_CleanDirty_Combined_df['Clean/Dirty']
FilterID_CleanDirty_Combined_df = FilterID_CleanDirty_Combined_df.drop(columns=['Clean/Dirty', 'Volts', 'Volts.1', 'Volts.2', 'Volts.3', 'Amps', 'Amps.1', 'Amps.2', 'Amps.3'])
FilterID_CleanDirty_Combined_df
Grouped_FilterID_CleanDirty = FilterID_CleanDirty_Combined_df[FilterID_CleanDirty_Combined_df['Cumulative Time in Test (sec)'] <= second_cut_off].groupby(['Date and Time', 'Filter ID'])

Grouped_FilterID_CleanDirty.sum()

FilterID_CleanDirty_df = pd.DataFrame(Grouped_FilterID_CleanDirty.sum())

FilterID_CleanDirty_df.to_excel("Data/Power and PD over Time.xlsx", index=True, header=True)

# Ploting Time Series Data


# HVAC Energy vs Time

FilteredData_df['Clean/Dirty Filter ID'] = FilteredData_df['Clean/Dirty'] + str(' ') + FilteredData_df['Filter ID']

Grouped1 = FilteredData_df[FilteredData_df['Cumulative Time in Test (sec)']<=second_cut_off].groupby(['Outdoor Temp', 'Clean/Dirty Filter ID'])

# samplelist = ['Clean FG-1', 'Clean FG-2', 'Clean MERV 8-1', 'Clean MERV 8-2', 'Clean MERV 13-1', 'Clean MERV 13-2',
#               'Dirty MERV 8-4', 'Dirty MERV 8-5', 'Dirty MERV 13-4', 'Dirty MERV 13-5']
samplelist = list(set(FilteredData_df['Clean/Dirty Filter ID']))

# seasons = [40.0, 95.0]
seasons = list(set(FilteredData_df['Outdoor Temp']))

for season in seasons:
    for sample in samplelist:

        power_plot = Grouped1.get_group((season, sample)).plot(kind='line', 
                                                  x='Cumulative Time in Test (sec)', 
                                                  y='Compressor and Fan Power (kW)',
                                                  ylim=(0,6.1), legend=False, 
                                                  title='Outdoor Temp of ' + str(season) + ' with a ' + sample
                                                 )
        power_plot.set_ylabel('Compressor and Fan Power (kW)')
        plt.tight_layout()
        plt.savefig("Images/Energy Plots/" + str(season) + " " + str(sample) + " Power Cycling over Time.png")
        
        PD_plot = Grouped1.get_group((season, sample)).plot(kind='line', 
                                                  x='Cumulative Time in Test (sec)', 
                                                  y='Filter Pressure Drop (in/H2O)',
                                                  ylim=(0,0.30), legend=False, 
                                                  title='Outdoor Temp of ' + str(season) + ' with a ' + sample
                                                 )
        PD_plot.set_ylabel('Filter Pressure Drop (in/H2O)')
        plt.tight_layout()
        plt.savefig("Images/Pressure Drop Plots/" + str(season) + " " + str(sample) + " Pressure Drops over Time.png")



# HVAC Energy vs Time

FilteredData_df['Clean/Dirty Filter ID'] = FilteredData_df['Clean/Dirty'] + str(' ') + FilteredData_df['Filter ID']

Grouped1 = FilteredData_df[FilteredData_df['Cumulative Time in Test (sec)']<=second_cut_off].groupby(['Outdoor Temp', 'Clean/Dirty Filter ID'])

# samplelist = ['Clean MERV 13-1', 'Clean MERV 13-2', 'Clean FG-1', 'Clean FG-2', 'Clean MERV 8-1', 'Clean MERV 8-2', 
#               'Dirty MERV 13-4', 'Dirty MERV 13-5', 'Dirty MERV 8-4', 'Dirty MERV 8-5']
samplelist = list(set(FilteredData_df['Clean/Dirty Filter ID']))

# seasons = [40.0, 95.0]
seasons = list(set(FilteredData_df['Outdoor Temp']))

for season in seasons:
    for sample in samplelist:

        power_plot = Grouped1.get_group((season, sample)).plot(kind='line', 
                                                  x='Cumulative Time in Test (sec)', 
                                                  y='Compressor and Fan Power (kW)',
                                                  ylim=(0,6.1), legend=False, 
                                                  title='Outdoor Temp of ' + str(season) + ' with a ' + sample
                                                 )
#         power_plot.set_ylabel('Compressor and Fan Power (kW)')
#         plt.tight_layout()
#         plt.savefig("Images/Energy Plots/" + str(season) + " " + str(sample) + " Power Cycling over Time.png")
        
        power_plot = Grouped1.get_group((season, sample)).plot(kind='line', 
                                                  x='Cumulative Time in Test (sec)', 
                                                  y='Filter Pressure Drop (in/H2O)',
                                                  ylim=(0,0.30), legend=False, 
                                                  title='Outdoor Temp of ' + str(season) + ' with a ' + sample
                                                 )
#         power_plot.set_ylabel('Filter Pressure Drop (in/H2O)')
        plt.tight_layout()
        plt.savefig("Images/Energy and Pressure Over Time/" + str(season) + " " + str(sample) + " Pressure Drops over Time.png")


# gather all non zero pressure drop values

pressuredrop_df = FilteredData_df[FilteredData_df['Cumulative Time in Test (sec)']<=second_cut_off]

pressuredrop_df = pressuredrop_df[pressuredrop_df['Filter Pressure Drop (in/H2O)']!=0.0]

pressuredrop_df = pressuredrop_df.drop(columns=['Volts', 'Volts.1', 'Amps', 'Amps.1', 'Volts.2', 'Volts.3', 'Amps.2', 'Amps.3'])
  
pressuredrop_df['Clean/Dirty Filter ID'] = pressuredrop_df['Clean/Dirty'] + str(' ') + pressuredrop_df['Filter ID']
    
pressuredrop_cooling_df = pressuredrop_df[pressuredrop_df['Outdoor Temp']==95.0]

pressuredrop_heating_df = pressuredrop_df[pressuredrop_df['Outdoor Temp']==40.0]

pressuredrop_heating_df
    

#Gathering Energy consumed by using groupby()
#Group the data for only the first 2 hours the filter was tested
second_cut_off = 7200
Grouped_df = FilteredData_df[FilteredData_df['Cumulative Time in Test (sec)'] <= second_cut_off].groupby(['Outdoor Temp','Clean/Dirty','Filter ID'])

#Calculate the Energy and convert from seconds to hours  
Energy_Consumped_df = pd.DataFrame((Grouped_df['Whole Home Power (kW)'].sum())/(3600))
Energy_Consumped_df = Energy_Consumped_df.rename(columns={'Whole Home Power (kW)': 'Whole Home Energy (kWh)'})

Energy_Consumped_df['Compressor Energy (kWh)'] = (Grouped_df['Compressor Power (kW)'].sum())/(3600)

Energy_Consumped_df['Blower Fan Energy (kWh)'] = (Grouped_df['Blower Fan Power (kW)'].sum())/(3600)

Energy_Consumped_df['Compressor and Fan Energy (kWh)'] = (Grouped_df['Compressor and Fan Power (kW)'].sum())/(3600)

Energy_Consumped_df.to_excel('Data/Energy Consumption per Filter.xlsx')


#create a new group with just values during the heating season
#Gathering Energy consumed by using groupby()
#Group the data for only the first 2 hours the filter was tested
second_cut_off = 7200
Heating_df = FilteredData_df[FilteredData_df['Outdoor Temp'] == 40.0]
GroupedHeating_df = Heating_df[Heating_df['Cumulative Time in Test (sec)'] <= second_cut_off].groupby(['Clean/Dirty','Filter ID'])

#Calculate the Energy and convert from seconds to hours  
Energy_Consumped_Heating_df = pd.DataFrame((GroupedHeating_df['Whole Home Power (kW)'].sum())/(3600))
Energy_Consumped_Heating_df = Energy_Consumped_Heating_df.rename(columns={'Whole Home Power (kW)': 'Whole Home Energy (kWh)'})

Energy_Consumped_Heating_df['Compressor Energy (kWh)'] = (GroupedHeating_df['Compressor Power (kW)'].sum())/(3600)

Energy_Consumped_Heating_df['Blower Fan Energy (kWh)'] = (GroupedHeating_df['Blower Fan Power (kW)'].sum())/(3600)

Energy_Consumped_Heating_df['Compressor and Fan Energy (kWh)'] = (GroupedHeating_df['Compressor and Fan Power (kW)'].sum())/(3600)

# Try this instead of creating a new column and doing .sort_values()
# df.reindex(['Mon', 'Wed', 'Thu', 'Fri'], level='day')
Energy_Consumped_Heating_df = Energy_Consumped_Heating_df.reindex(['FG-1', 'FG-2', 'MERV 8-1', 'MERV 8-2', 'MERV 13-1', 'MERV 13-2',
                                    'MERV 8-4', 'MERV 8-5', 'MERV 13-4', 'MERV 13-5'], level='Filter ID')



#create a new group with just values during the cooling season
#Gathering Energy consumed by using groupby()
#Group the data for only the first 2 hours the filter was tested
second_cut_off = 7200
Cooling_df = FilteredData_df[FilteredData_df['Outdoor Temp'] == 95.0]
time_cut_off_Cooling_df = Cooling_df[Cooling_df['Cumulative Time in Test (sec)'] <= second_cut_off]
GroupedCooling_df = Cooling_df[Cooling_df['Cumulative Time in Test (sec)'] <= second_cut_off].groupby(['Clean/Dirty','Filter ID'])

#Calculate the Energy and convert from seconds to hours  
Energy_Consumped_Cooling_df = pd.DataFrame((GroupedCooling_df['Whole Home Power (kW)'].sum())/(3600))
Energy_Consumped_Cooling_df = Energy_Consumped_Cooling_df.rename(columns={'Whole Home Power (kW)': 'Whole Home Energy (kWh)'})

Energy_Consumped_Cooling_df['Compressor Energy (kWh)'] = (GroupedCooling_df['Compressor Power (kW)'].sum())/(3600)

Energy_Consumped_Cooling_df['Blower Fan Energy (kWh)'] = (GroupedCooling_df['Blower Fan Power (kW)'].sum())/(3600)

Energy_Consumped_Cooling_df['Compressor and Fan Energy (kWh)'] = (GroupedCooling_df['Compressor and Fan Power (kW)'].sum())/(3600)

Energy_Consumped_Cooling_df = Energy_Consumped_Cooling_df.reindex(['FG-1', 'FG-2', 'MERV 8-1', 'MERV 8-2', 'MERV 13-1', 'MERV 13-2',
                                    'MERV 8-4', 'MERV 8-5', 'MERV 13-4', 'MERV 13-5'], level='Filter ID')



# Ploting Grouped Results


#graph pressure drop across filter results from the heating season
pressuredrop_heating_df

order = ['Clean FG-1', 'Clean FG-2', 'Clean MERV 8-1', 'Clean MERV 8-2', 'Clean MERV 13-1', 'Clean MERV 13-2', 
         'Dirty MERV 8-4', 'Dirty MERV 8-5', 'Dirty MERV 13-4', 'Dirty MERV 13-5']

pressuredrop_heating_group = pressuredrop_heating_df.groupby(['Clean/Dirty Filter ID'])

pressuredrop_heating_group_df = pressuredrop_heating_group.mean()
pressuredrop_heating_group_df = pressuredrop_heating_group_df.reindex(order)

pd_heating_group_err_df = pressuredrop_heating_group['Filter Pressure Drop (in/H2O)'].std()
pd_heating_group_err_df = pd_heating_group_err_df.reindex(order)

error = list(pd_heating_group_err_df)

heat_PD_plot= pressuredrop_heating_group_df['Filter Pressure Drop (in/H2O)'].plot(kind='bar',
                                                                    color=['grey', 'grey', 'r', 'r', 'b', 'b', 'lightcoral', 'lightcoral', 'cornflowerblue', 'cornflowerblue'],
                                                                    figsize = (14,7),
                                                                    yerr=error
                                                                   )

plt.xlabel('Filters Tested')
plt.title('Heating Season: Pressure Drop Averages')
heat_PD_plot.set_ylabel('Pressure Drop of Filter (in/H2O)')
plt.grid(True)
plt.tight_layout()
plt.savefig('Images/Pressure Drop Plots/HeatingSeason_Pressure_Drop.png')


#graph pressure drop across filter results from the cooling season

pressuredrop_cooling_group = pressuredrop_cooling_df.groupby(['Clean/Dirty Filter ID'])

pressuredrop_cooling_group_df = pressuredrop_cooling_group.mean()
pressuredrop_cooling_group_df = pressuredrop_cooling_group_df.reindex(order)

pd_cooling_group_err_df = pressuredrop_cooling_group['Filter Pressure Drop (in/H2O)'].std()
pd_cooling_group_err_df = pd_cooling_group_err_df.reindex(order)

error = list(pd_cooling_group_err_df)


cool_PD_plot = pressuredrop_cooling_group_df['Filter Pressure Drop (in/H2O)'].plot(kind='bar',
                                                                    color=['grey', 'grey', 'r', 'r', 'b', 'b', 'lightcoral', 'lightcoral', 'cornflowerblue', 'cornflowerblue'],
                                                                    yerr=error,
                                                                    figsize = (14,7)
                                                                   )

plt.xlabel('Filters Tested')
plt.title('Cooling Season: Pressure Drop Averages')
cool_PD_plot.set_ylabel('Pressure Drop of Filter (in/H2O)')
plt.grid(True)
plt.tight_layout()
plt.savefig('Images/Pressure Drop Plots/CoolingSeason_Pressure_Drop.png')


#graph Energy_Consumped_Heating_df results

heat_HVACenergy_plot = Energy_Consumped_Heating_df['Compressor and Fan Energy (kWh)'].plot(kind='bar', 
                                                                    color=['grey', 'grey', 'r', 'r', 'b', 'b', 'lightcoral', 'lightcoral', 'cornflowerblue', 'cornflowerblue'],
                                                                    figsize = (14,7)
                                                                   )
plt.xlabel('Filters Tested')
plt.xticks(range(len(order)), order)
plt.title('Heating Season: HVAC Energy Consumed')
heat_HVACenergy_plot.set_ylabel('Compressor and Fan Energy (kWh)')
plt.grid(True)
plt.tight_layout()
plt.savefig('Images/Energy Plots/Heating_Season_HVAC_Energy')


#graph Energy_Consumped_Cooling_df results for HVAC unit

cool_HVACenergy_plot = Energy_Consumped_Cooling_df['Compressor and Fan Energy (kWh)'].plot(kind='bar', 
                                                                    color=['grey', 'grey', 'r', 'r', 'b', 'b', 'lightcoral', 'lightcoral', 'cornflowerblue', 'cornflowerblue'],
                                                                    figsize=(14,7)
                                                                   )

cool_HVACenergy_plot.set_ylabel('Compressor and Fan Energy (kWh)')
plt.xlabel('Filters Tested')
plt.xticks(range(len(order)), order)
plt.title('Cooling Season: HVAC Energy Consumed')
plt.grid(True)
plt.tight_layout()
plt.savefig('Images/Energy Plots/Cooling_Season_HVAC_Energy.png')


#graph Energy_Consumped_Heating_df results for Whole Home

heat_HomeEnergy_plot = Energy_Consumped_Heating_df['Whole Home Energy (kWh)'].plot(kind='bar', 
                                                            color=['grey', 'grey', 'r', 'r', 'b', 'b', 'lightcoral', 'lightcoral', 'cornflowerblue', 'cornflowerblue'],
                                                            figsize=(14,7)
                                                                   )
plt.xlabel('Filters Tested')
plt.xticks(range(len(order)), order)
plt.title('Heating Season: Whole Home Energy Consumed')
heat_HomeEnergy_plot.set_ylabel('Whole Home Energy(kWh)')
plt.grid(True)
plt.tight_layout()
plt.savefig('Images/Energy Plots/Heating_Season_WholeHome_Energy')


#graph Energy_Consumped_Cooling_df results for Whole Home

cool_HomeEnergy_plot = Energy_Consumped_Cooling_df['Whole Home Energy (kWh)'].plot(kind='bar',
                                                            y='Whole Home Energy (kWh)',
                                                            color=['grey', 'grey', 'r', 'r', 'b', 'b', 'lightcoral', 'lightcoral', 'cornflowerblue', 'cornflowerblue'], 
                                                            figsize=(14,7)
                                                                   )
plt.xlabel('Filters Tested')
plt.xticks(range(len(order)), order)
plt.title('Cooling Season: Whole Home Energy Consumed')
cool_HomeEnergy_plot.set_ylabel('Whole Home Energy (kWh)')
plt.grid(True)
plt.tight_layout()
plt.savefig('Images/Energy Plots/Cooling_Season_WholeHome_Energy')

