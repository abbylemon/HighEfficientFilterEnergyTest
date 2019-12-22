import pandas as pd

FG_data_file = "../Data-20191120134426.csv"

FG_data_file_pd = pd.read_csv(FG_data_file)
FG_data_file_pd.head()