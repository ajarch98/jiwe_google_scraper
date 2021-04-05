from tables import DbManager
from tables import Threat, Value, Date, Country

from plotly import graph_objects as go
from loguru import logger


class Visualizer():
    def __init__(self):
        self.db_manager = DbManager()
        self.session = self.db_manager.get_session()

    def get_threats(self):
        """Get ids of threats with associated values."""
        self.threat_ids = []
        for threat in self.session.query(Threat).all():
            if threat.values:
                self.threat_ids.append(threat.id)

    def get_dates(self):
        """Get last seven dates in database."""
        self.dates = []
        for date in self.session.query(Date).order_by(Date.value.desc()).limit(7):
            if date.values:
                self.dates.append(date.value)

    def visualize(self):
        _values = {}
        dates = self.session.query(Date).order_by(Date.value.desc()).limit(7).all()
        for date in dates:
            for country in self.session.query(Country).all():
                for threat in self.session.query(Threat).all():
                    try:
                        value = self.session.query(Value).filter(
                                    Value.country == country,
                                    Value.date == date,
                                    Value.threat == threat
                                ).one()
                        print(value.__dict__, value.country.name)
                        # input()
                        # print(country.name, date.value, threat.id, value.value)
                    except Exception:
                        logger.info(
                            f'Missing value for params: {(country.name, date.value, threat.id)}'
                            )
                        raise

        fig = go.Figure(
            data=[
                go.Bar(
                    x=self.dates,
                    y=self.session.query(Value).filter(
                            Value.country.name == "Kenya",
                            Value.date.value._in(self.dates)
                            ).all()
                )
            ]
        )

        fig.show()


if __name__ == "__main__":
    visualizer = Visualizer()
    visualizer.get_threats()
    visualizer.get_dates()
    visualizer.visualize()
