from flask import Flask, request
import subprocess
import signal
import os

app = Flask(__name__)

process = None
current_freq = None



def start_stream(freq):
    global process, current_freq

    # Stop previous stream
    if process:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)

    current_freq = freq

    cmd = f"""
    rtl_fm -f {freq}e6 -M wbfm -s 240000 -r 48000 - |
    ffmpeg -f s16le -ar 48k -ac 1 -i - -f mp3 -b:a 128k \
    icecast://source:hackme@0.0.0.0:8000/stream
    """

    process = subprocess.Popen(
        cmd,
        shell=True,
        executable="/bin/bash",
        preexec_fn=os.setsid
    )

def render_page(message):
    host = request.host.split(":")[0]  # gets IP/domain only
    ICECAST_URL = f"http://{host}:8000/stream"

    return f"""
    <html>
    <head>
        <title>RTL-SDR Radio</title>
        <style>
            body {{
                font-family: Arial;
                background: #111;
                color: #eee;
                text-align: center;
                padding-top: 40px;
            }}
            a {{
                color: #4CAF50;
                text-decoration: none;
            }}
            .box {{
                border: 1px solid #444;
                padding: 25px;
                display: inline-block;
                border-radius: 12px;
                background: #1a1a1a;
                width: 320px;
            }}
            button {{
                padding: 10px;
                margin: 5px;
                border: none;
                border-radius: 6px;
                background: #4CAF50;
                color: white;
                cursor: pointer;
                width: 120px;
            }}
            button:hover {{
                background: #66bb6a;
            }}
            input {{
                padding: 8px;
                width: 140px;
                border-radius: 5px;
                border: none;
                margin-top: 10px;
            }}
            #clock {{
                font-size: 16px;
                color: #ccc;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2><a href="/">{message}</a></h2>

            <p>Current Frequency: <b>{current_freq if current_freq else "None"} MHz</b></p>

            <p>
                ▶ <a href="{ICECAST_URL}" target="_blank">Listen to Stream</a>
            </p>

            <audio controls autoplay>
                <source src="{ICECAST_URL}" type="audio/mpeg">
            </audio>

            <hr>

            <h3>📻 Presets</h3>

            <div id="clock">
                <p>🇮🇳 IST: <span id="istTime"></span></p>
                <p>🌍 GMT: <span id="gmtTime"></span></p>
            </div>


            <div>
                <a href="/tune/92.7"><button>Big FM<br>92.7</button></a>
                <a href="/tune/93.5"><button>Red FM<br>93.5</button></a>
                <a href="/tune/94.3"><button>Club FM<br>94.3</button></a>
                <a href="/tune/98.3"><button>Radio Mirchi FM<br>98.3</button></a>
                <a href="/tune/101.9"><button>Ananthapuri<br>101.9</button></a>
            </div>

            <hr>

            <h3>🎯 Manual Tune</h3>

            <form action="/tune" method="get">
                <input type="text" name="freq" placeholder="Enter MHz">
                <br>
                <button type="submit">Tune</button>
            </form>

            <br>

            <a href="/stop">⛔ Stop Stream</a>
        </div>
        <script>
        function updateClocks() {{
            const now = new Date();

            const ist = new Date(now.toLocaleString("en-US", {{ timeZone: "Asia/Kolkata" }}));
            const gmt = new Date(now.toLocaleString("en-US", {{ timeZone: "UTC" }}));

            document.getElementById("istTime").innerText = ist.toLocaleTimeString();
            document.getElementById("gmtTime").innerText = gmt.toLocaleTimeString();
        }}

        setInterval(updateClocks, 1000);
        updateClocks();
        </script>
    </body>
    </html>
    """


@app.route("/")
def home():
    return render_page("Welcome")


@app.route("/tune/<freq>")
def tune(freq):
    try:
        start_stream(freq)
        return render_page(f"Tuned to {freq} MHz")
    except Exception as e:
        return f"<h3>Error: {e}</h3>"


@app.route("/tune")
def tune_query():
    freq = request.args.get("freq")
    if freq:
        return tune(freq)
    return render_page("No frequency provided")


@app.route("/stop")
def stop():
    global process, current_freq

    if process:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process = None
        current_freq = None

    return render_page("Stream stopped")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
