import pandas as pd
import os.path as path
import numpy as np
import pandas as pd
import pandas as pd
import os.path as path
import numpy as np
from datetime import datetime, timezone
import matplotlib.pyplot as plt

def calc_market_share(input_data, condition='ilevel_0 in ilevel_0'):
    market_share = {}
    data = input_data.query(condition)
    idx = {col: data.columns.get_loc(col) for col in data.columns}
    #print(data.head(50).to_string())

    for row in data.values:
        supplier = row[idx['SupplierName']]
        market_share.setdefault(supplier, [0, 0])
        market_share[supplier][0] += row[idx['ValueMax']]
        market_share[supplier][1] += row[idx['NumberOfEmployees']]

    #print(market_share.values())
    sum_value = sum(x[0] for x in list(market_share.values()))
    price_per_employee = {k: v[0] / v[1] for k, v in market_share.items()}
    market_share = {k: v[0] / sum_value for k, v in market_share.items()}

    # print("Condition: {}".format(data['Region'].unique()))
    # print("Shares: {}".format(market_share))
    return market_share, price_per_employee

def load_data():
    data_dir = "."
    publishers = pd.read_csv(path.join(data_dir, "publishers.csv"), sep=';')
    contracts = pd.read_csv(path.join(data_dir, "contracts.csv"), sep=';')
    return publishers, contracts


def create_query_string(relevantICs):
    query = ""
    for ic in relevantICs:
        if len(query) > 0:
            query += " or "
        query += "SupplierIC == {}".format(ic)
    return query


def preprocess_data(publishers, contracts, relevantICs):
    query_string = create_query_string(relevantICs)

    # filter irrelevant contracts
    flt = contracts.query(query_string).reset_index()

    # filter-out contracts without monetary information
    flt = flt.dropna(subset=['ValueVatExcluded', 'ValueVatIncluded'], how='all')

    # convert Value columns to numeric and convert NaNs to 0
    flt[["ValueVatIncluded", "ValueVatExcluded"]] = flt[["ValueVatIncluded", "ValueVatExcluded"]].apply(
        pd.to_numeric).fillna(0)

    # Values with VAT and without VAT aren't very consistent, take max of both columns
    value_max_col = flt[['ValueVatExcluded', 'ValueVatIncluded']].max(axis=1)

    # convert to UTC datetime
    flt['Date'] = pd.to_datetime(flt['PublishedAtUtc'], utc=True)

    # drop unnecessary columns
    flt = flt.drop(['index', 'ValueVatExcluded', 'ValueVatIncluded', 'PublishedAtUtc'], axis=1)

    # insert value max column instead of two Value columns
    flt.insert(4, 'ValueMax', value_max_col)

    # merge with publishers
    merged = flt.merge(publishers, on='PublisherIC', how='inner')
    return merged


def which_quartal(date):
    return "Q{} {}".format(int(date.month / 3 + 1), date.strftime('%y'))


# main function
publishers, contracts = load_data()

# ICs of companies in the food voucher business
relevantICs = np.array([61860476, 62913671, 24745391], dtype=np.int)

clean_data = preprocess_data(publishers, contracts, relevantICs)
calc_market_share(clean_data)

first_contract = pd.to_datetime(clean_data.sort_values('Date', ascending=True).head(1).Date.values[0], utc=True)
last_contract = pd.to_datetime(clean_data.sort_values('Date', ascending=False).head(1).Date.values[0], utc=True)
start = datetime(first_contract.year, int(first_contract.month / 3) * 3 + 1, day=1, tzinfo=timezone.utc)
one_quartal = pd.DateOffset(months=3)
end = datetime(last_contract.year, last_contract.month, day=1, tzinfo=timezone.utc) + pd.DateOffset(months=1)

share_per_quartal = {}
employee_price = {}

while start < end:
    next_quartal = start + one_quartal
    #print("time period: from {}, to {}, pretty: {}".format(start, next_quartal, start.strftime('%B %Y')))
    share_per_quartal[which_quartal(start)], employee_price[which_quartal(start)] = calc_market_share(clean_data, "Date > @start and Date < @next_quartal")
    start += one_quartal

suppliers = clean_data.SupplierName.unique()
plt.title('Market Shares in Years')
for supplier in suppliers:
    plt.plot(list(share_per_quartal.keys()), [100 * x[supplier] for x in list(share_per_quartal.values())])
plt.xlabel('Quartals')
plt.ylabel('Market Share [%]')
plt.gca().legend(suppliers)
plt.gca().set_ylim([0, 100])
plt.show()

data_by_region = {}
price_per_region = {}

distinct_regions = clean_data['Region'].unique()
for item in distinct_regions:
    data_by_region[item], price_per_region[item] = calc_market_share(clean_data, "Region == @item")
#print(data_by_region)

for item in distinct_regions:
    plt.title('{}'.format(item))
    plt.pie(x=data_by_region[item].values(), labels=list(data_by_region[item].keys()), autopct='%1.1f%%',
        shadow=True, center = (0, 0))
    plt.show()

#print(clean_data.head(10).to_string())ß

plt.title('Price per Employee in Years')
for supplier in suppliers:
    plt.plot(list(employee_price.keys()), [x[supplier] for x in list(employee_price.values())])
plt.xlabel('Quartals')
plt.ylabel('Price [CZK]')
plt.gca().legend(suppliers)
#plt.gca().set_ylim([0, 100])
plt.show()