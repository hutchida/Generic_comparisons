
import pandas as pd
import time

def add(log_filepath, metric, metric_type, details): 
    if metric > 0:
        print('\nAdding metrics to log...')
        date = str(time.strftime("%Y-%m-%d"))
        df_metric = pd.read_csv(log_filepath) #Load the log
        #check metric hasn't been added to the df already for that document on that date
        df_metric.date = df_metric.date.astype(str)
        df_metric.details = df_metric.details.astype(str)
        new_row = {'metric_type':metric_type, 'details':details,'metric': metric, 'date': date}
        if any((df_metric.date == date) & (df_metric.details == details)) == False: 
            df_metric.loc[len(df_metric)] = new_row #add new row to the end of the dataframe
            #df_metric.loc[1] = new_row #add new row to the start of the dataframe
            df_metric = df_metric.sort_values('date', ascending = False)
            df_metric.to_csv(log_filepath,index=False)
        else:
            print('NO METRICS ADDED: date and details already exist in a row')
#EXAMPLE
#add(log_dir+r'\pastdate-metrics.csv', 1, 'PastDate update', str(len(df_master)) + ' affected docs this week')
