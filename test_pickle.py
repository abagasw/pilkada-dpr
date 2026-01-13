import pickle
data = pickle.load(open('dashboard/data/dashboard_data.pkl', 'rb'))
print('✅ Pickle loaded successfully!')
print(f'Keys: {list(data.keys())}')
df = data['df_unified']
print(f'Rows in df_unified: {len(df):,}')
print(f'Sentiment distribution: {data["sentiment_dist"]}')
