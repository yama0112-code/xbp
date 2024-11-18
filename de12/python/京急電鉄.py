import pandas as pd

#cvsファイルの読み込み
df = pd.read_csv("de12/pp/京急久里浜.csv")
 
station_name="久里浜"
start_time="8:00"
end_time="9:00"

filtered_df=df[(df["駅名"]== station_name) &
(df["時刻"]>=start_time)&
(df["時刻"]<=end_time)]

if not filtered_df.empty:
    print(filtered_df)
else:
    print("該当するダイヤがありません。")