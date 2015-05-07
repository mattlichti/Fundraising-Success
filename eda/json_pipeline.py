import pandas as pd
import numpy as np
import json
import glob
import os

def import_loans(address):
    '''
    Input address of folder full of json files
    Output dataframe of kiva loans
    ''' 
    lst = []
    for file in glob.glob(address + "/*.json"):
        f = open(file)
        dic = json.loads(f.readline())
        lst +=(dic['loans'])
    df = pd.DataFrame(lst)
    df = df.drop_duplicates(['id'])        
    return df

def get_desc(df):
    '''
    extracts the English description and drops the description
    in other languages
    '''
    text_df = pd.DataFrame(list(df.description.map(lambda x: x['texts'])))
    df['description'] = text_df['en'] # null for text without any English
    return df

def payment_terms(df):
    '''
    Extracts repayment interval (monthly, irregularly, or lump sum),
    repayment term (in months), and potential currency loss info 
    and drops the rest of the repayment info
    '''
    terms = pd.DataFrame(list(df.terms))
    df['repayment_interval'] = terms['repayment_interval']
    df['repayment_term'] = terms['repayment_term']
    curr_loss = pd.DataFrame(list(terms.loss_liability))
    df['currency_loss'] = curr_loss.currency_exchange
    df.drop('terms',axis=1,inplace=True)
    return df

def borrower_info(df):
    ''' 
    Extracts country, group size, gender, and drops other borrower info
    '''
    df['country'] = df.location.map(lambda x: x['country_code'])
    df['group_size'] = df.borrowers.map(lambda x: len(x))
    df['gender'] = df.borrowers.map(lambda x: x[0]['gender'])
    df.drop(['borrowers', 'location'],axis=1,inplace=True)
    return df

def transform_dates(df):
    '''
    Converts posted date to datetime object
    calculates the number of days the loan is available on kiva from the 
    posted date until planned expiration date as timedelta object
    '''
    df['posted_date'] = pd.to_datetime(df.posted_date)
    df['planned_expiration_date'] = pd.to_datetime(df.planned_expiration_date)
    df['days_available'] = ((df.planned_expiration_date - df.posted_date)/
                            np.timedelta64(1, 'D')).round().astype(int)
    df.drop('planned_expiration_date',axis=1,inplace=True)
    return df

def filter_by_date(df):
    min_date = '2012-01-25' # when kiva expiration policy fully implemented
    max_date = '2014-12-22' # last day when all loans in dataset could expire
    df = df[(df.posted_date < max_date) & (df.posted_date > min_date)]
    return df

def build_df(address, model='simple'):
    '''
    Loads and transforms the data, drops the data that was generated after loan
    was funded (since that data will not be available for future predictions)
    '''
    droplist = ['basket_amount','currency_exchange_loss_amount','delinquent',
                'paid_date', 'paid_amount', 'journal_totals', 'payments',
                'lender_count', 'funded_date','funded_amount','translator', 
                'video', 'tags']
    df = import_loans(address)
    df.drop(droplist,axis=1,inplace=True)
    df = payment_terms(df)
    df = borrower_info(df)
    df = transform_dates(df)
    df = filter_by_date(df)


    if model == 'complex': # model that uses description text
        df = get_desc(df)
        df['image'] = df.image.map(lambda x: x['id'])
    else:
        df.drop(['image', 'name', 'partner_id', 'description'], axis=1, inplace=True)
    
    df = df.set_index('id')
    return df

def get_start_date(df):
    '''outputs the date when kiva fully implemented their expiration policy'''

def dump_to_pickle(df, filename):
    ''' save cleaned dataframe as pickle'''
    df.to_pickle('data/' + filename + '.pkl')

def load_pickles(lst):
    '''input list of locations of pickled dataframes
       output dataframe that merges all the pickles
       useful when cleaning data in batches'''
    dfs = []
    for pick in lst:
        df = pd.io.pickle.read_pickle('data/pickles/'+ pick +'.pkl')
        dfs.append(df)
    df = pd.concat(dfs,axis=0)
    return df

def save_as_json(df, filename):
    '''save cleaned dataframe as json'''
    loans = df.to_json()
    os.chdir(address + 'dumps')
    with open(filename, 'w') as outfile:
        json.dump(loans, outfile)

def transform_jsons(folders):
    for folder in folders:
        lst = import_loans(folder)
        df = build_df(lst)
        dump_to_json(df,folder +'.json')

def load_cleaned(lst,drops = [],reindex=False):
    os.chdir(address + 'dumps')
    dfs = []
    for jsn in lst:
        f = open(jsn + '.json')
        dic = json.loads(f.read())
        f.close()
        df = pd.read_json(dic)
        if drops != []:
            df.drop(drops,axis=1,inplace=True)
        dfs.append(df)
    # return pd.concat(dfs,axis=0)
    df = pd.concat(dfs,axis=0)
    df.posted_date = pd.to_datetime(df.posted_date*10**6)
    if reindex:
        df = df.drop_duplicates(['id'])        
        df = df.set_index('id')
    return df

def condense_jsons(file_list):
    df = load_cleaned(file_list, drops = ['image', 'name', 'partner_id'],
                                 reindex=True)
    dump(df,'everything.json')

def load_cleaned(lst,drops = [],reindex=False):
    os.chdir(address + 'dumps')
    dfs = []
    for jsn in lst:
        f = open(jsn + '.json')
        dic = json.loads(f.read())
        f.close()
        df = pd.read_json(dic)
        if drops != []:
            df.drop(drops,axis=1,inplace=True)
        dfs.append(df)
    # return pd.concat(dfs,axis=0)
    df = pd.concat(dfs,axis=0)
    df.posted_date = pd.to_datetime(df.posted_date*10**6)
    if reindex:
        df = df.drop_duplicates(['id'])        
        df = df.set_index('id')
    return df

def condense_jsons(file_list):
    df = load_cleaned(file_list, drops = ['image', 'name', 'partner_id'],
                                 reindex=True)
    dump(df,'everything.json')