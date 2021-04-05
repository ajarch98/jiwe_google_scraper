from scraper import KasperskyScraper
from visualizer import Visualizer
from tables import DbManager

if __name__ == "__main__":
    countries = ['Kenya', 'Nigeria', 'South Africa']
    scraper = KasperskyScraper(countries)
    scraper.fill_values_in_database()

    visualizer = Visualizer()
    visualizer.visualize()
