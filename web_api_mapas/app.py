from flask import Flask, render_template, request
import requests
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST', 'GET'])
def buscar():
    if request.method == 'POST':
        lugar = request.form['lugar']
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': lugar,
            'format': 'json',
            'limit': 1
        }
        headers = {
            "User-Agent": "Flask-Educational-App"
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()

            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                nombre = data[0]['display_name']
                bbox = data[0].get('boundingbox', [])

                gas_stations = []
                hospitals = []

                if bbox:
                    try:
                        south, north, west, east = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])

                        overpass_url = "https://overpass-api.de/api/interpreter"

                        gas_query = f"""
                        [out:json][timeout:25];
                        (
                          node["amenity"="fuel"]({south},{west},{north},{east});
                          way["amenity"="fuel"]({south},{west},{north},{east});
                          relation["amenity"="fuel"]({south},{west},{north},{east});
                        );
                        out center;
                        """

                        print(f"Fetching gas stations for bbox: {south},{west},{north},{east}")
                        gas_response = requests.post(overpass_url, data=gas_query, headers=headers, timeout=25)
                        
                        if gas_response.status_code == 200:
                            gas_data = gas_response.json()
                            print(f"Gas stations found: {len(gas_data.get('elements', []))}")
                            
                            for element in gas_data.get('elements', []):
                                element_lat = None
                                element_lon = None
                                
                                if element.get('type') == 'node':
                                    element_lat = element.get('lat')
                                    element_lon = element.get('lon')
                                elif 'center' in element:
                                    element_lat = element['center'].get('lat')
                                    element_lon = element['center'].get('lon')
                                
                                if element_lat and element_lon:
                                    tags = element.get('tags', {})
                                    station = {
                                        'lat': float(element_lat),
                                        'lon': float(element_lon),
                                        'display_name': tags.get('name', tags.get('brand', 'Gasolinera sin nombre')),
                                        'phone': tags.get('phone', ''),
                                        'opening_hours': tags.get('opening_hours', '')
                                    }
                                    gas_stations.append(station)

                        else:
                            print(f"Error fetching gas stations: {gas_response.status_code}")

                        time.sleep(1)

                        hospital_query = f"""
                        [out:json][timeout:25];
                        (
                          node["amenity"="hospital"]({south},{west},{north},{east});
                          way["amenity"="hospital"]({south},{west},{north},{east});
                          relation["amenity"="hospital"]({south},{west},{north},{east});
                        );
                        out center;
                        """

                        print(f"Fetching hospitals for bbox: {south},{west},{north},{east}")
                        hosp_response = requests.post(overpass_url, data=hospital_query, headers=headers, timeout=25)
                        
                        if hosp_response.status_code == 200:
                            hosp_data = hosp_response.json()
                            print(f"Hospitals found: {len(hosp_data.get('elements', []))}")
                            
                            for element in hosp_data.get('elements', []):
                                element_lat = None
                                element_lon = None
                                
                                if element.get('type') == 'node':
                                    element_lat = element.get('lat')
                                    element_lon = element.get('lon')
                                elif 'center' in element:
                                    element_lat = element['center'].get('lat')
                                    element_lon = element['center'].get('lon')
                                
                                if element_lat and element_lon:
                                    tags = element.get('tags', {})
                                    hospital = {
                                        'lat': float(element_lat),
                                        'lon': float(element_lon),
                                        'display_name': tags.get('name', 'Hospital sin nombre')
                                    }
                                    hospitals.append(hospital)
                        else:
                            print(f"Error fetching hospitals: {hosp_response.status_code}")

                    except Exception as e:
                        print(f"Error fetching from Overpass: {e}")

                bbox_str = ','.join(bbox) if bbox else ''

                print(f"Returning {len(gas_stations)} gas stations and {len(hospitals)} hospitals")

                return render_template(
                    'mapa.html',
                    lat=lat,
                    lon=lon,
                    nombre=nombre,
                    gas_stations=gas_stations,
                    hospitals=hospitals,
                    bbox=bbox_str
                )
            else:
                return render_template('mapa.html', error=True, gas_stations=[], hospitals=[])
                
        except Exception as e:
            print(f"Error in search: {e}")
            return render_template('mapa.html', error=True, gas_stations=[], hospitals=[])

    return render_template('mapa.html', gas_stations=[], hospitals=[])

if __name__ == '__main__':
    app.run(debug=True)
