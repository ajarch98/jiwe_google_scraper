import pandas as pd
import streamlit as st

from collections import OrderedDict

from db_manager import DBManager, NewsItem
from scraper import GoogleScraper

st.set_page_config(layout="wide")

db_manager = DBManager()

def get_db_data(approved=None):
    session = db_manager.get_session()
    data = session.query(NewsItem).order_by(
        NewsItem.scraping_time.desc()
    )
    if approved is True:
        data = data.filter(NewsItem.is_approved == True)
    elif approved is False:
        data = data.filter(NewsItem.is_approved == None)
    else:
        pass # no logic required

    data = data.all()
    session.close()
    return data

def clean_data_to_df(data):
    df_dicts = []
    for row in data:
        df_row = OrderedDict()
        for key in ('title', 'url', 'publishing_time', 'scraping_time', 'is_approved'):
            df_row[key] = getattr(row, key)
        df_dicts.append(df_row)
    df = pd.DataFrame.from_dict(df_dicts)

    return df

def make_clickable(link):
    '''Renders clickable links.'''
    return f'<a target="blank" href="{link}">url</a>'


def main():
    st.title('Jiwe Scraper Control Center')
    button = st.button('Click here to manually re-run the scraper')
    if button: # rescrape data on button press
        scraping_text = st.text('Rescraping the web...')
        scraper = GoogleScraper()
        scraper.scrape_news_from_rss()
        scraping_text.text('Rescraped, thank you!!')

    st.header('VIEWS')
    option = st.radio(
        'Pick your poison:',
        ('View all rows',
         'View rows requiring approval',
         'View approved rows')
    )

    if option == 'View all rows':
        data = get_db_data()
        data = clean_data_to_df(data)
        if data.empty:
            st.write('Sorry, no rows scraped yet :(')
        else:
            data = data.drop(columns=['scraping_time'])
            data['url'] = data['url'].apply(make_clickable)
            st.write(data.to_html(escape=False, index=False), unsafe_allow_html=True)
    elif option == 'View approved rows':
        data = get_db_data(approved=True)
        data = clean_data_to_df(data)
        if data.empty:
            st.write('Sorry, no rows approved yet :(')
        else:
            data = data.drop(columns=['scraping_time'])
            data['url'] = data['url'].apply(make_clickable)
            st.write(data.to_html(escape=False, index=False), unsafe_allow_html=True)
    elif option == 'View rows requiring approval':
        rows = get_db_data(approved=False)
        if not rows:
            st.write('No rows to approve!!')
        else:
            responses = []
            for _, row in enumerate(rows):
                responses.append(st.selectbox(
                        'Approve?',
                        ('SKIP', 'YES', 'NO'),
                        key=f'box_{_}'
                    )
                )
                _row = row.__dict__
                keys_to_skip = ['id', '_sa_instance_state', 'scraping_time']
                st.write({k:v for k, v in row.__dict__.items() if k not in keys_to_skip})

            session = db_manager.get_session()
            for _, resp in enumerate(responses):
                if resp != 'SKIP':
                    if resp == 'YES':
                        rows[_].is_approved = True
                        del responses[_]
                    elif resp == 'NO':
                        rows[_].is_approved = False
                        del responses[_]
                    else:
                        raise
                    session.add(rows[_])
                    session.commit()
                else:
                    pass  # No code required
    else:
        raise


if __name__ == "__main__":
    main()


