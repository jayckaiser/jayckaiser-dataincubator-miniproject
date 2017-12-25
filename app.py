"""

Jay Kaiser

app.py

Created 12/23/2017

"""

import requests
import simplejson as json
import pandas as pd
from flask import Flask, render_template, request
from bokeh.plotting import figure
from bokeh.embed import components
from datetime import date
from dateutil.relativedelta import relativedelta

app = Flask(__name__)


@app.route('/')
def to_main_page():
    return render_template('index.html')


@app.route('/index', methods=['GET', 'POST'])
def index_run():
    """
    Runs the actual server as necessary.

    :return:
    """
    if request.method == 'GET':
        print('Getting the webpage!')
        return render_template('index.html')

    else:
        print("Let's collect some data!")

        # Gathering the ticker information.
        ticker = request.form.get('name_info')
        print("Let's try {}!".format(ticker))

        if ticker is None:
            print('No ticker found. Defaulting to A.')
            ticker = 'A'
        ticker_df = retrieve_stocks(ticker)

        # Modifying the ticker to be only in the current month.
        last_month_stocks = last_monthify(ticker_df)

        # Finding the options to plot.
        current_options = retrieve_options()

        # Plotting the graph.
        script, div = plot_into_bokeh(last_month_stocks, current_options)
        return render_template("graph.html", script=script, div=div)


def retrieve_stocks(ticker):
    """
    Given a ticker string, use the API to gather all stock data about that ticker.

    :param ticker: (string) the ticker to search for, defaults to 'A' if not found
    :return: (pd.DataFrame)
    """

    # Assuming the user is not being cheeky...
    if not ticker.isalpha():
        ticker = 'A'
    ticker = ticker.upper()

    # Gathering the info via the API
    raw_query = 'https://www.quandl.com/api/v3/datatables/WIKI/PRICES.json?ticker={}&api_key=cUdP6PvqQ59JzZCjYGib'
    r = requests.get(raw_query.format(ticker))
    json_r = json.loads(r.text).get('datatable')

    # Converting the info into a beautiful DataFrame.

    columns = [column.get('name') for column in json_r.get('columns')]
    data = json_r.get('data')  # list of lists

    # When encountering something not found in the dataset.
    if len(data) == 0:
        print('That stock ticker was not found. Defaulting to A.')
        return retrieve_stocks('A')
    else:
        print('Found stock data for ticker {}.'.format(ticker))
        return pd.DataFrame(data, columns=columns)


def last_monthify(ticker_df):
    """
    Retrieves data from the dataframe for only last month (and converts the date row to datetime).

    :param ticker_df: (pd.DataFrame) the full data for a given stock index ticker
    :return pd.DataFrame:
    """

    last_month = date.today() + relativedelta(months=-1)

    ticker_df['date'] = pd.to_datetime(ticker_df['date'])

    if len(request.values.getlist('all_data')) > 0:
        print('Showing all data!')
        return ticker_df

    else:
        print('Modified stock data for most recent month only.')
        return ticker_df[ticker_df['date'] > last_month]


def retrieve_options():
    options = request.values.getlist('option')

    print('Here are the options to be graphed:')
    print(options)
    return options


def plot_into_bokeh(ticker_df, options):
    """
    Given the dataframe and options to plot, embed a Bokeh graph into the server.

    :param ticker_df: (pd.DataFrame) the dataframe to plot (all necessary processing done beforehand)
    :param options: (list(string)) the specific columns to plot (if none selected, does all)
    :return:
    """

    # Given the chance the user is being cheeky...
    if len(options) == 0:
        options = ['close', 'open', 'high', 'low', 'adj_close', 'adj_open', 'adj_high', 'adj_low']

    # options to make the graph nicer to look at.
    dates = ticker_df['date']
    ticker = ticker_df.iloc[0]['ticker']
    colors = ['blue', 'red', 'green', 'yellow', "black", "pink", 'teal', 'orange']
    possible_options = {
        "close": "Closing price",
        "open": "Opening price",
        "adj_close": "Adjusted closing price",
        "adj_open": "Adjusted opening price",
        "high": "High",
        "low": "Low",
        "adj_high": "Adjusted high",
        "adj_low": "Adjusted low"
        }

    # Actual plotting of the graph.
    plot = figure(title='Quandi WIKI EOD Stock Prices (One Month Ago to Today)',
                  x_axis_label='date',
                  x_axis_type='datetime')

    for index, option in enumerate(options):
        plot.line(dates.values, ticker_df[option].values,
                  line_width=4,
                  line_color=colors[index],
                  legend='{}: {}'.format(ticker, possible_options.get(option)))

    plot.legend.border_line_alpha = 0.1
    plot.legend.location = 'top_left'

    script, div = components(plot)
    return script, div


if __name__ == "__main__":
    app.run(port=33507)

