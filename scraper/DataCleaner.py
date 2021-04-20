import os

import pandas as pd


def data_filler(source, aux, interval, dump):
    data_source = pd.DataFrame()
    data_aux = pd.DataFrame()

    # Loading up data from source folder
    for filename in os.listdir(source):
        if not filename.endswith('.csv'):
            continue
        else:
            filepath = os.path.join(source, filename)
            data_source = data_source.append(pd.read_csv(filepath), ignore_index=True)

    # Loading up data from auxiliary folder
    for filename in os.listdir(aux):
        if not filename.endswith('.csv'):
            continue
        else:
            filepath = os.path.join(aux, filename)
            data_aux = data_aux.append(pd.read_csv(filepath), ignore_index=True)

    cur_val = min(data_source.loc[0]["Time"], data_aux.loc[0]["Time"])
    end_val = max(data_source.loc[data_source.shape[0] - 1]["Time"],
                  data_aux.loc[data_aux.shape[0] - 1]["Time"])

    data_cumulative = pd.DataFrame(columns=['Time', 'Bids', 'Asks'])

    while cur_val <= end_val:
        row = data_source.loc[data_source["Time"] == cur_val]

        # Try again on auxiliary
        if row.empty:
            row = data_aux.loc[data_aux["Time"] == cur_val]

        # If neither have it print missing
        if row.empty:
            print('Missing:', cur_val)
        # Else something found it so add it in to cumulative set
        else:
            data_cumulative = data_cumulative.append(row, ignore_index=True)

        cur_val += interval

        # If we reach a row count equalling dump we save to csv and dump
        if data_cumulative.shape[0] > 0 and data_cumulative.shape[0] % dump == 0:
            file_name = str(data_cumulative.loc[0]["Time"]) + '.csv'
            data_cumulative.to_csv(file_name, index=False)
            print('File:', file_name, 'saved.')
            data_cumulative.drop(data_cumulative.index, inplace=True)

    # dumping remainder of what is collected
    file_name = str(data_cumulative.loc[0]["Time"]) + '.csv'
    data_cumulative.to_csv(file_name, index=False)
    print('File:', file_name, 'saved.')
    data_cumulative.drop(data_cumulative.index, inplace=True)


def data_length(path):
    data_source = pd.DataFrame()

    for filename in os.listdir(path):
        if not filename.endswith('.csv'):
            continue
        else:
            filepath = os.path.join(path, filename)
            data_source = data_source.append(pd.read_csv(filepath), ignore_index=True)

    print(data_source.shape[0])


def data_missing(path, interval):
    # ToDo this operation seems terribly inefficient and can likely be improved
    #  by utilizing indexing
    data_source = pd.DataFrame()

    for filename in os.listdir(path):
        if not filename.endswith('.csv'):
            continue
        else:
            filepath = os.path.join(path, filename)
            data_source = data_source.append(pd.read_csv(filepath), ignore_index=True)

    cur_val = data_source.loc[0]["Time"]
    end_val = data_source.loc[data_source.shape[0] - 1]["Time"]

    missing = 0

    while cur_val != end_val:
        row = data_source.loc[data_source["Time"] == cur_val]

        if row.empty:
            print('Missing:', cur_val)
            missing += 1

        cur_val += interval

    print("Total missing values", missing)




