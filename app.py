from flask import Flask, request, render_template
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
from math import radians, cos, sin, sqrt, atan2
import pandas as pd
import subprocess
import os

app = Flask(__name__)
api = Api(app)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # radius of the Earth in km
    dlon = radians(lon2) - radians(lon1)
    dlat = radians(lat2) - radians(lat1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def extract_bindata(bin_file):
    mavlogdump_path = r"C:\Users\nithi\AppData\Local\Programs\Python\Python312\Scripts\__pycache__\mavlogdump.cpython-312.pyc"
    csv_file = 'temp.csv'
    temp_bin_file = 'temp.bin'
    with open(bin_file, 'rb') as f:
        bin_data = f.read()
    with open(temp_bin_file, 'wb') as f:
        f.write(bin_data)
        
    log_types = ['ATT', 'BAT', 'CTUN', 'TECS', 'GPS', 'CMD']
    dfs = []
    for log_type in log_types:
        with open(csv_file, 'w') as f:
            subprocess.run(['python', mavlogdump_path, '--types', log_type, '--format', 'csv', temp_bin_file], stdout=f)
        df = pd.read_csv(csv_file)
        df.columns = [f'{log_type}.{col}' for col in df.columns]
        dfs.append(df)
    df = pd.concat(dfs, axis=1)

    # Calculate the number of kilometers traveled
    df['GPS.Dist'] = df['GPS.Spd'] * df['GPS.TimeUS'] / (1000 * 60 * 60)
    # df['GPS.Dist'] = [haversine(df['GPS.Lat'][i-1], df['GPS.Lon'][i-1], df['GPS.Lat'][i], df['GPS.Lon'][i]) for i in range(1, len(df))]
    km_travelled = df['GPS.Dist'].sum()

    # Get the mAh consumed
    mah_consumed = df['BAT.CurrTot'].max()

    # Calculate the flight time
    flight_time = df['GPS.TimeUS'].max() - df['GPS.TimeUS'].min()

    return km_travelled, mah_consumed, flight_time


# class FlightLogAnalyzer(Resource):
#     def post(self):
#         bin_file = request.files['file']
#         filename = secure_filename(bin_file.filename)
#         bin_file.save(filename)
#         df, df_CTUN, df_CMD, df_waypoints = extract_bindata(filename)
#         return {'data': df.to_dict(), 'CTUN': df_CTUN.to_dict(), 'CMD': df_CMD.to_dict(), 'waypoints': df_waypoints.to_dict()}
@app.route('/')
def home():
    return render_template('index.html')

class FlightLogAnalyzer(Resource):
    def post(self):
        bin_file = request.files['file']
        filename = secure_filename(bin_file.filename)
        bin_file.save(filename)
        km_travelled, mah_consumed, flight_time = extract_bindata(filename)
        return render_template('analyze.html', km_travelled=km_travelled, mah_consumed=mah_consumed, flight_time=flight_time)

# class FlightLogAnalyzer(Resource):
#     def post(self):
#         bin_file = request.files['file']
#         filename = secure_filename(bin_file.filename)
#         bin_file.save(filename)
#         km_travelled, mah_consumed, flight_time = extract_bindata(filename)
#         return {'km_travelled': km_travelled, 'mah_consumed': mah_consumed, 'flight_time': flight_time}


api.add_resource(FlightLogAnalyzer, '/analyze')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)



