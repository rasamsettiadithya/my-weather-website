# Weather app

The page shows temperatures for the cities you check, and which of those cities is warmest. The browser never calls the weather service itself. It sends the city names to your backend. The backend calls Open-Meteo, compares the temperatures, and sends JSON back.

## Folders

```text
weather/
  frontend/                 the page the browser shows
    index.html              sends / to the weather page
    weather.html            checkboxes, cards, and the call table
    weather.css             styles
    weather.js              sends the city names and paints the JSON
  backend/
    weather_service.py      city coordinates, Open-Meteo calls, warmest-city sentence
  runtime/
    frontend_server.py      serves the page on port 8000
    backend_server.py       answers /weather on port 8001
    render_server.py        serves the page and /weather for Render
    control.py              starts and stops those two programs
    server.py               opens the same control panel
  start.html                Start, Stop, and the clickable frontend link
  Start Weather.command     double-click this to open the control panel
  ARCHITECTURE.md           this file
```

`index.html` and `style.css` in the project root are a different page. They are not part of this weather app.

## How to run it

Double-click `weather/Start Weather.command`, or open [http://127.0.0.1:8090/](http://127.0.0.1:8090/) when the control panel is already running.

On that page, Frontend and Backend are checked. **Start** frees ports 8000 and 8001, then starts whatever you checked. **Stop** closes those two ports so the next start is clean. The control panel stays on port 8090.

The frontend link on that page is [http://127.0.0.1:8000/weather.html](http://127.0.0.1:8000/weather.html).

If you open `start.html` from the disk, Safari is looking at a file, not at port 8090. Reload it. The file sends you to the live control page.

## Ports

| Piece | Address | What it does |
|---|---|---|
| Control panel | http://127.0.0.1:8090/ | Start and Stop |
| Frontend | http://127.0.0.1:8000/weather.html | The weather page |
| Backend | http://127.0.0.1:8001/weather | The weather API |

## What happens when you check the weather

```text
Browser                         Your computer                      Open-Meteo
weather.html
  checkboxes
       |
       |  HTTP POST /weather
       |  { "cities": ["hyderabad", "delhi"] }
       v
                          backend_server.py :8001
                                 |
                                 |  weather_service.py
                                 |  looks up latitude and longitude
                                 |
                                 |  HTTPS GET, one request per city
                                 |  latitude, longitude, current=temperature_2m
                                 v
                                                          api.open-meteo.com
                                                          returns temperature_2m
                                 |
                                 |  rounds each temperature
                                 |  writes the warmest-city sentence
                                 v
       JSON with temperatures,
       the sentence, and the
       Open-Meteo calls
       <
```

The comparison stays on the backend. The page only displays what comes back.

## Render

The local control panel stays on your computer. Render runs one free Python web service from [render.yaml](../render.yaml). The start command is `python3 weather/runtime/render_server.py`.

That process listens on `0.0.0.0` and Render's `PORT`. It serves the files in `frontend/` and answers `GET` and `POST /weather` with the same JSON as port 8001. Opening `/` redirects to `/weather.html`.

On localhost the page still posts to `http://127.0.0.1:8001/weather`. On Render the page posts to `/weather` on the same site. The live site is [https://my-weather-website-app.onrender.com](https://my-weather-website-app.onrender.com).

## Frontend calling the backend

Protocol: HTTP. Method: POST. URL on your computer: `http://127.0.0.1:8001/weather`. URL on Render: `/weather`.

Request body:

```json
{
  "cities": ["hyderabad", "melbourne"]
}
```

City ids you can send: `hyderabad`, `visakhapatnam`, `denver`, `melbourne`, `delhi`.

Response:

```json
{
  "requested": ["hyderabad", "melbourne"],
  "cities": [
    { "id": "hyderabad", "temperature": 32 },
    { "id": "melbourne", "temperature": 23 }
  ],
  "result": "Hyderabad is the warmest at 32°.",
  "openMeteo": []
}
```

`temperature` is already rounded. `result` is the full sentence, including a tie if two or more cities share the highest temperature. `openMeteo` lists the calls the backend made. An empty city list returns `Select at least one city.`

In Postman, use POST, the URL above, header `Content-Type: application/json`, and the same body. GET `http://127.0.0.1:8001/weather?cities=hyderabad,melbourne` also works.

## Backend calling Open-Meteo

Protocol: HTTPS. Method: GET. One call for each selected city.

```text
https://api.open-meteo.com/v1/forecast?latitude=17.385&longitude=78.4867&current=temperature_2m
```

There is no JSON body. Latitude and longitude are on the server, not in the browser.

| City | Latitude | Longitude |
|---|---|---|
| Hyderabad | 17.385 | 78.4867 |
| Visakhapatnam | 17.6868 | 83.2185 |
| Denver, USA | 39.7392 | -104.9903 |
| Melbourne, Australia | -37.8136 | 144.9631 |
| Delhi, India | 28.6139 | 77.209 |

Open-Meteo answers with `current.temperature_2m`, plus `time` and `interval`. The backend reads the temperature and ignores the other two fields for the comparison. The page still shows the full Open-Meteo JSON in the call table.

## What the page shows

At the bottom of the weather page:

- The JSON request the page will send. It updates as you check cities.
- The JSON the backend returns, after you click Check Weather.
- A table named Each call. Each row has the call, the protocol, the method, the request, and the response.

The first row is the frontend calling the backend. The rows after it are the backend calling Open-Meteo, one row per selected city.
