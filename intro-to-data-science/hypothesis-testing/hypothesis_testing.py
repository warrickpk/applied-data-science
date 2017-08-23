import pandas as pd
from scipy import stats

states = {'OH': 'Ohio', 'KY': 'Kentucky', 'AS': 'American Samoa', 'NV': 'Nevada', 'WY': 'Wyoming', 'NA': 'National',
          'AL': 'Alabama', 'MD': 'Maryland', 'AK': 'Alaska', 'UT': 'Utah', 'OR': 'Oregon', 'MT': 'Montana',
          'IL': 'Illinois', 'TN': 'Tennessee', 'DC': 'District of Columbia', 'VT': 'Vermont', 'ID': 'Idaho',
          'AR': 'Arkansas', 'ME': 'Maine', 'WA': 'Washington', 'HI': 'Hawaii', 'WI': 'Wisconsin', 'MI': 'Michigan',
          'IN': 'Indiana', 'NJ': 'New Jersey', 'AZ': 'Arizona', 'GU': 'Guam', 'MS': 'Mississippi', 'PR': 'Puerto Rico',
          'NC': 'North Carolina', 'TX': 'Texas', 'SD': 'South Dakota', 'MP': 'Northern Mariana Islands', 'IA': 'Iowa',
          'MO': 'Missouri', 'CT': 'Connecticut', 'WV': 'West Virginia', 'SC': 'South Carolina', 'LA': 'Louisiana',
          'KS': 'Kansas', 'NY': 'New York', 'NE': 'Nebraska', 'OK': 'Oklahoma', 'FL': 'Florida', 'CA': 'California',
          'CO': 'Colorado', 'PA': 'Pennsylvania', 'DE': 'Delaware', 'NM': 'New Mexico', 'RI': 'Rhode Island',
          'MN': 'Minnesota', 'VI': 'Virgin Islands', 'NH': 'New Hampshire', 'MA': 'Massachusetts', 'GA': 'Georgia',
          'ND': 'North Dakota', 'VA': 'Virginia'}

def get_list_of_university_towns():
    uni_towns = pd.read_table('./data/university_towns.txt', header=None)
    uni_towns = uni_towns.T.iloc[0]
    tmp_str_array = []
    tmp_state = "Alabama"
    for i in uni_towns:
        if "[edit]" in i:
            tmp_state = i.replace("[edit]", "")
            continue
        tmp_region = i[0:i.find("(")]
        if tmp_region[-1] == " ":
            tmp_region = tmp_region[:-1]
        tmp_str_array.append([tmp_state, tmp_region])
    columns = ["State", "RegionName"]
    return pd.DataFrame(data=tmp_str_array, columns=columns)

def get_recession_start():
    gdp = pd.read_excel('./data/gdplev.xls', skiprows=220, header=None, parse_cols=[4, 6], names=["Quarter", "GDP"])
    gdp = gdp.set_index("Quarter")
    gdp = gdp.T.iloc[0]
    gdp_diff = gdp.diff()
    in_rec = False
    rec_start = "None"
    for i in range(1, len(gdp_diff[1:]) - 1):
        if int(gdp_diff[i]) < 0 and int(gdp_diff[i + 1]) < 0:
            if not in_rec:
                in_rec = True
                rec_start = gdp_diff.index[i]
        elif in_rec and int(gdp_diff[i]) > 0 and int(gdp_diff[i + 1]) > 0:
            in_rec = False
    return rec_start

def get_recession_end():
    gdp = pd.read_excel('./data/gdplev.xls', skiprows=220, header=None, parse_cols=[4, 6], names=["Quarter", "GDP"])
    gdp = gdp.set_index("Quarter")
    gdp = gdp.T.iloc[0]
    gdp_diff = gdp.diff()
    in_rec = False
    rec_end = "None"
    for i in range(1, len(gdp_diff[1:]) - 1):
        if int(gdp_diff[i]) < 0 and int(gdp_diff[i + 1]) < 0:
            if not in_rec:
                in_rec = True
        elif in_rec and int(gdp_diff[i]) > 0 and int(gdp_diff[i + 1]) > 0:
            in_rec = False
            rec_end = gdp_diff.index[i + 1]
    return rec_end

def get_recession_bottom():
    gdp = pd.read_excel('./data/gdplev.xls', skiprows=220, header=None, parse_cols=[4, 6], names=["Quarter", "GDP"])
    gdp = gdp.set_index("Quarter")
    gdp = gdp.T.iloc[0]
    rec_start = get_recession_start()
    rec_end = get_recession_end()
    in_rec = False
    rec_bottom = gdp.index[0]
    min_gdp = gdp[0]
    for i in range(1, len(gdp)):
        if gdp.index[i] == rec_start:
            in_rec = True
            rec_bottom = gdp.index[i]
            min_gdp = gdp[i]
        elif in_rec and gdp[i] < min_gdp:
            rec_bottom = gdp.index[i]
            min_gdp = gdp[i]
        if in_rec and gdp.index[i] == rec_end:
            in_rec = False
    return rec_bottom

def convert_housing_data_to_quarters():
    house_prices = pd.read_csv('./data/City_Zhvi_AllHomes.csv')
    house_prices = pd.concat([house_prices.ix[:, 1:3], house_prices.ix[:, 51:252]], axis=1)
    house_states = pd.Series(house_prices['State'], index=house_prices.index)
    house_prices['State'] = house_states.map(states)
    house_prices = house_prices.set_index(['State', 'RegionName'])
    house_prices = pd.concat([house_prices.ix[:, i:i+3].mean(axis=1) for i in range(0, len(house_prices.columns), 3)],
                             axis=1)
    new_cols = [str(x)+y for x in range(2000, 2017) for y in ('q1', 'q2', 'q3', 'q4')]
    new_cols = new_cols[:-1]
    house_prices.columns = new_cols
    return house_prices

def run_ttest():
    house_data = convert_housing_data_to_quarters().sort_index()
    rec_start = get_recession_start()
    rec_start_less_one = int(rec_start[rec_start.find("q") + 1]) - 1
    if rec_start_less_one == 0:
        rec_start_less_one = str(int(rec_start[:rec_start.find("q")]) - 1) + "q4"
    else:
        rec_start_less_one = rec_start[:rec_start.find("q") + 1] + str(rec_start_less_one)
    rec_bottom = get_recession_bottom()
    price_change = house_data[rec_start_less_one].div(house_data[rec_bottom])
    price_change = pd.DataFrame(index=price_change.index, data=price_change)
    univ_towns = get_list_of_university_towns().set_index(['State', 'RegionName'])
    univ_towns_price_change = pd.merge(price_change, univ_towns, how='inner', left_index=True, right_index=True)
    non_univ_towns_price_change = price_change.drop(univ_towns_price_change.index)
    ttest = stats.ttest_ind(univ_towns_price_change.reset_index()[0].dropna(),
                      non_univ_towns_price_change.reset_index()[0].dropna())
    return (True if ttest.pvalue < 0.01 else False, ttest.pvalue,
          "university town" if univ_towns_price_change.mean()[0] < non_univ_towns_price_change.mean()[0] else
          "non-university town")

print(run_ttest())
