import pandas as pd


df0 = pd.read_csv('instaglam0.csv')
df_1 = pd.read_csv('instaglam_1.csv')

res = pd.concat([df0,df_1]).drop_duplicates(keep=False)
print(res)


# df = df0.merge(df_1, how = 'inner' ,indicator=False)
# print(df)


# df = pd.concat([df0, df_1])
#
# df = df.reset_index(drop=True)
#
# df_group = df.groupby(list(df.columns))
#
# idx = [x[0] for x in df_group.groups.values() if len(x) > 1]
# print(df.reindex(idx))