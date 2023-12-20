import pandas as pd

api_base = 'https://api.weather.gc.ca/collections/'

class HMS:
    def __init__(self, identifier = None):
        self.id = identifier
        self.info, self.lon, self.lat, self.name, self.number, self.region, self.status, self.datum, self.links = None, None, None, None, None, None, None, None, None
        self.level, self.discharge = None, None
        if identifier is not None: self.update_info(identifier = identifier)
        return

    def search_stations(self, identifier = None, region = None, name = None, number = None, status = None):
        limit, offset = 100, 0
        url = api_base + 'hydrometric-stations/items?'
        if identifier is not None: url += 'IDENTIFIER={}&'.format(identifier)
        if region is not None: url += 'PROV_TERR_STATE_LOC={}&'.format(region)
        if name is not None: url += 'STATION_NAME={}&'.format(name)
        if number is not None: url += 'STATION_NUMBER={}&'.format(number)
        if status is not None: url += 'STATUS_EN={}&'.format(status)
        url += 'f=csv&limit={}&offset={}'

        try: df = pd.read_csv(url.format(limit, offset))
        except: df = pd.DataFrame([])

        if len(df) == limit:
            offset += limit
            while True:
                try:
                    df = pd.concat([df, pd.read_csv(url.format(limit, offset))])
                    offset += limit
                except: break
        return df
    
    def update_info(self, identifier):
        info = self.search_stations(identifier = identifier).loc[0].copy()
        if not info.empty:
            self.id = info['IDENTIFIER']
            self.info = info.copy()
            self.lon, self.lat = info['x'], info['y']
            self.name = info['STATION_NAME']
            self.number = info['STATION_NUMBER']
            self.region = info['PROV_TERR_STATE_LOC']
            self.status = info['STATUS_EN']
            self.datum = info['VERTICAL_DATUM']
            self.links = info['links']
            self.level, self.discharge = None, None
        else: print('Warning: No STATION IDENTIFIER is found!')
        return
    
    def retreive_daily_mean(self, begin_date, end_date):
        limit, offset = 100, 0
        url = api_base + 'hydrometric-daily-mean/items?'
        url += 'datetime={}/{}&'.format(pd.Timestamp(begin_date).strftime('%Y-%m-%d'), pd.Timestamp(end_date).strftime('%Y-%m-%d'))
        url += 'STATION_NUMBER={}&'.format(self.number)
        url += 'f=csv&limit={}&offset={}'

        try: df = pd.read_csv(url.format(limit, offset))
        except: df = pd.DataFrame([])

        if len(df) == limit:
            offset += limit
            while True:
                try:
                    df = pd.concat([df, pd.read_csv(url.format(limit, offset))])
                    offset += limit
                except: break
        if not df.empty:
            df.index = pd.to_datetime(df['DATE'])
            df = df.drop(columns = 'DATE')
            self.level = df['LEVEL']
            self.discharge = df['DISCHARGE']
        return df
    

if __name__ == '__main__':
    #station = HMS(identifier = None)
    #df_inventory = station.search_stations(name = 'ADAMS')
    #print(df_inventory.iloc[:, :-1].to_string())
    #station.update_info(identifier = '08LD003')

    station = HMS(identifier = '08LD003')
    begin_date = '1979-01-01'
    end_date = '1980-01-01'
    df_hydro_daily_mean = station.retreive_daily_mean(begin_date = begin_date, end_date = end_date)