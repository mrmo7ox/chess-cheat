import os
import sys
import json
import threading
import atexit
import signal
from time import sleep
import webview
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from chess_bot import CheatBot

app = Flask(__name__, static_folder="web")
CORS(app)

CONFIG_FILE = "config.json"
ACC_FILE = "acc.json"
bot_instance = None
stockfish_engine = None
current_depth = 9
depth_lock = threading.Lock()

ui_logs = []


def sys_log(msg):
    ui_logs.append(msg)
    print(msg)


def force_cleanup():
    global bot_instance
    if bot_instance:
        bot_instance.cleanup()


atexit.register(force_cleanup)


def handle_kill_signals(signum, frame):
    force_cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, handle_kill_signals)
signal.signal(signal.SIGTERM, handle_kill_signals)


def get_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except:
            pass
    return default


def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def init_stockfish_with_depth(depth):
    global stockfish_engine, current_depth
    try:
        if bot_instance:
            sf = bot_instance.init_stockfish()
            if sf:
                with depth_lock:
                    stockfish_engine = sf
                    current_depth = depth
                    stockfish_engine.set_depth(depth)
                sys_log(f"Stockfish initialised with depth {depth}")
                return True
    except Exception as e:
        sys_log(f"Stockfish init error: {e}")
    return False


@app.route("/")
def index():
    return send_from_directory("web", "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("web", path)


@app.route("/api/logs", methods=["GET"])
def get_logs():
    global ui_logs
    logs_to_send = ui_logs.copy()
    ui_logs.clear()
    return jsonify({"logs": logs_to_send})


@app.route("/api/config", methods=["GET", "POST"])
def manage_config():
    default_config = {
        "play_mode": "Auto-Play",
        "depth": 9,
        "color": "#ff2a2a",
        "delay": 1800,
        "browser_path": "",
        "stockfish_path": "",
        "hotkeys": {"next": "Shift + Space", "toggle": "Alt + T", "hide": "F12"},
    }
    if request.method == "POST":
        save_json(CONFIG_FILE, request.json)
        return jsonify({"status": "success"})
    return jsonify(get_json(CONFIG_FILE, default_config))


@app.route("/api/account", methods=["GET", "POST"])
def manage_account():
    if request.method == "POST":
        save_json(ACC_FILE, request.json)
        return jsonify({"status": "success"})
    return jsonify(get_json(ACC_FILE, {"username": "", "pass": ""}))


@app.route("/api/set-depth", methods=["POST"])
def set_depth():
    global stockfish_engine, current_depth
    data = request.json
    new_depth = int(data.get("depth", 9))
    with depth_lock:
        if stockfish_engine:
            try:
                stockfish_engine.set_depth(new_depth)
                current_depth = new_depth
                sys_log(f"Depth updated to {new_depth} (live)")
                return jsonify({"status": "ok", "depth": new_depth})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "Engine not initialised"}), 400


@app.route("/api/open", methods=["POST"])
def api_open():
    global stockfish_engine, bot_instance, current_depth
    if bot_instance:
        bot_instance.cleanup()
    config = get_json(CONFIG_FILE, {})
    browser_path = config.get("browser_path", "")
    stockfish_path = config.get("stockfish_path", "")  # <-- get stockfish path
    bot_instance = CheatBot(stockfish_path=stockfish_path, browser_path=browser_path)
    depth_val = int(config.get("depth", 9))
    bot_instance.depth = depth_val

    sf = bot_instance.init_stockfish()
    if sf:
        with depth_lock:
            stockfish_engine = sf
            current_depth = depth_val
            stockfish_engine.set_depth(depth_val)
    else:
        sys_log("WARNING: Stockfish could not be loaded. Moves will fail.")

    def run_browser():
        bot_instance.init_browser()
        bot_instance.login()

    threading.Thread(target=run_browser, daemon=True).start()
    return jsonify({"message": "Browser environment established."})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    global bot_instance
    if bot_instance and bot_instance.page:
        try:
            bot_instance.page.run_js("""
                window.botActive = false;
                const styles = document.getElementById('nemesis-styles');
                if (styles) styles.remove();
                const btn = document.getElementById('stealth-trigger-btn');
                if (btn) btn.remove();
            """)
            sys_log("NEMESIS Engine Halted & Uninjected.")
        except:
            pass
    return jsonify({"message": "Engine stopped."})


@app.route("/get-move", methods=["POST"])
def get_move():
    global stockfish_engine, current_depth
    if not stockfish_engine:
        return jsonify({"error": "Engine offline"}), 500
    try:
        fen = request.json.get("fen")
        with depth_lock:
            # ensure depth is still set (in case it changed)
            stockfish_engine.set_depth(current_depth)
            stockfish_engine.set_fen_position(fen)
            best = stockfish_engine.get_best_move()
        if best and len(best) >= 4:
            move_str = f"Move: {best[:2]} -> {best[2:4]}"
            sys_log(
                f"<span style='color:#00ff80'>[{move_str}]</span> FEN: <span style='color:#666'>{fen}</span>"
            )
            return jsonify({"analysis": {"move": {"from": best[:2], "to": best[2:4]}}})
        else:
            return jsonify({"error": "No move found"}), 400
    except Exception as e:
        sys_log(f"<span style='color:red'>[ERROR] {str(e)}</span>")
        return jsonify({"error": str(e)}), 500


@app.route("/api/inject", methods=["POST"])
def api_inject():
    global bot_instance
    if not bot_instance or not bot_instance.page:
        return jsonify({"message": "Error: Browser not running."}), 400

    config = get_json(CONFIG_FILE, {})
    play_mode = config.get("play_mode", "Auto-Play")
    color = config.get("color", "#ff2a2a")
    delay = config.get("delay", 1800)

    js_code = f"""
    (function() {{
        "use strict";
        const oldStyles = document.getElementById('nemesis-styles');
        if (oldStyles) oldStyles.remove();
        const oldBtn = document.getElementById('stealth-trigger-btn');
        if (oldBtn) oldBtn.remove();
        window.currentBotMode = "{play_mode}";
        window.botActive = (window.currentBotMode === "Auto-Play");
        let isCalculating = false;
        let autoPlayInterval = null;
        const styles = document.createElement('style');
        styles.id = 'nemesis-styles';
        styles.innerHTML = `
            .nemesis-start {{
                filter: drop-shadow(0 0 10px {color}) !important;
                background-color: {color}4D !important;
                border-radius: 50%;
            }}
            .nemesis-target {{
                background-color: {color}66 !important;
                border: 2px solid {color}99 !important;
                z-index: 9999 !important;
                pointer-events: none;
            }}
            #stealth-trigger-btn {{
                position: fixed;
                bottom: 15px;
                right: 15px;
                width: 40px;
                height: 40px;
                background: rgba(0,0,0,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 50%;
                cursor: pointer;
                z-index: 1000000;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                color: rgba(255,255,255,0.2);
                font-size: 10px;
                font-family: sans-serif;
            }}
            #stealth-trigger-btn:hover {{
                background: {color}33;
                color: rgba(255,255,255,0.8);
                border-color: {color};
            }}
        `;
        document.head.appendChild(styles);
        
        function getFEN() {{
            const pieces = document.querySelectorAll('.piece');
            const board = Array(8).fill().map(() => Array(8).fill(null));
            const pieceMap = {{
                'wp':'P','wn':'N','wb':'B','wr':'R','wq':'Q','wk':'K',
                'bp':'p','bn':'n','bb':'b','br':'r','bq':'q','bk':'k'
            }};
            pieces.forEach(piece => {{
                const cls = Array.from(piece.classList);
                const pieceType = cls.find(c => pieceMap[c]);
                const squareClass = cls.find(c => c.startsWith('square-'));
                if (pieceType && squareClass) {{
                    const match = squareClass.match(/square-(\\d)(\\d)/);
                    if (match) {{
                        let x = parseInt(match[1]) - 1;
                        let y = parseInt(match[2]) - 1;
                        board[7 - y][x] = pieceMap[pieceType];
                    }}
                }}
            }});
            let fen = '';
            for (let r = 0; r < 8; r++) {{
                let empty = 0;
                for (let c = 0; c < 8; c++) {{
                    if (board[r][c] === null) empty++;
                    else {{
                        if (empty > 0) fen += empty;
                        fen += board[r][c];
                        empty = 0;
                    }}
                }}
                if (empty > 0) fen += empty;
                if (r < 7) fen += '/';
            }}
            let turn = 'w';
            if (document.querySelector('.clock-black.clock-player-turn')) turn = 'b';
            return `${{fen}} ${{turn}} - - 0 1`;
        }}
        
        function getMyColor() {{
            const board = document.querySelector('wc-chess-board') || document.querySelector('.board');
            if (!board) return 'w';
            if (board.classList.contains('flipped') || board.getAttribute('orientation') === 'black') return 'b';
            return 'w';
        }}
        
        function getSquareClass(algebraic) {{
            if (!algebraic || algebraic.length < 2) return null;
            const files = {{ a:1,b:2,c:3,d:4,e:5,f:6,g:7,h:8 }};
            return `square-${{files[algebraic[0]]}}${{algebraic[1]}}`;
        }}
        
        async function fetchAndDisplayMove(shouldExecute = false) {{
            if (isCalculating) return;
            isCalculating = true;
            const fen = getFEN();
            // Retry logic with exponential backoff
            let attempts = 0;
            const maxAttempts = 3;
            let data = null;
            while (attempts < maxAttempts && !data) {{
                try {{
                    const response = await fetch('http://127.0.0.1:5000/get-move', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ fen: fen }})
                    }});
                    if (!response.ok) throw new Error('HTTP ' + response.status);
                    const json = await response.json();
                    if (json.analysis && json.analysis.move) {{
                        data = json.analysis.move;
                        break;
                    }}
                }} catch(e) {{
                    attempts++;
                    if (attempts < maxAttempts) await new Promise(r => setTimeout(r, 500 * attempts));
                }}
            }}
            if (!data) {{
                isCalculating = false;
                return;
            }}
            const fromSq = data.from;
            const toSq = data.to;
            const fromClass = getSquareClass(fromSq);
            const toClass = getSquareClass(toSq);
            const board = document.querySelector('wc-chess-board') || document.querySelector('.board');
            if (!board) {{
                isCalculating = false;
                return;
            }}
            const piece = board.querySelector(`.piece.${{fromClass}}`);
            if (piece) piece.classList.add('nemesis-start');
            const targetDiv = document.createElement('div');
            targetDiv.className = `highlight nemesis-target ${{toClass}}`;
            board.appendChild(targetDiv);
            if (shouldExecute) {{
                const randDelay = Math.floor(Math.random() * (2000 - 600 + 1)) + 600;
                setTimeout(() => {{
                    if (!window.botActive || window.currentBotMode !== "Auto-Play") return;
                    executeClickMove(fromSq, toSq);
                }}, randDelay);
            }}
            setTimeout(() => {{
                if (piece) piece.classList.remove('nemesis-start');
                if (targetDiv.parentNode) targetDiv.remove();
            }}, {delay});
            isCalculating = false;
        }}
        
        function executeClickMove(fromSq, toSq) {{
            const board = document.querySelector('wc-chess-board');
            if (!board) return;
            const rect = board.getBoundingClientRect();
            const size = rect.width / 8;
            const myColor = getMyColor();
            const files = {{ a:0,b:1,c:2,d:3,e:4,f:5,g:6,h:7 }};
            const getCenter = (alg) => {{
                const file = files[alg[0]];
                const rank = parseInt(alg[1]) - 1;
                const x = myColor === 'w' ? file : 7 - file;
                const y = myColor === 'w' ? 7 - rank : rank;
                return {{
                    x: rect.left + (x * size) + (size/2),
                    y: rect.top + (y * size) + (size/2)
                }};
            }};
            const from = getCenter(fromSq);
            const to = getCenter(toSq);
            const dispatchClick = (pt) => {{
                const opts = {{ bubbles:true, cancelable:true, clientX:pt.x, clientY:pt.y, pointerId:1, pointerType:'mouse', isPrimary:true, button:0, buttons:1 }};
                board.dispatchEvent(new PointerEvent('pointerdown', opts));
                board.dispatchEvent(new PointerEvent('pointerup', opts));
            }};
            dispatchClick(from);
            dispatchClick(to);
        }}
        
        function startAutoPlay() {{
            if (autoPlayInterval) clearInterval(autoPlayInterval);
            autoPlayInterval = setInterval(() => {{
                if (!window.botActive || window.currentBotMode !== "Auto-Play") return;
                const fen = getFEN();
                const turn = fen.split(' ')[1];
                if (turn !== getMyColor()) return;
                if (isCalculating) return;
                fetchAndDisplayMove(true);
            }}, 1500);
        }}
        
        function stopAutoPlay() {{
            if (autoPlayInterval) {{
                clearInterval(autoPlayInterval);
                autoPlayInterval = null;
            }}
        }}
        
        if (window.currentBotMode === "Auto-Play") startAutoPlay();
        
        const btn = document.createElement('div');
        btn.id = 'stealth-trigger-btn';
        btn.innerText = '⟳';
        btn.addEventListener('click', () => {{
            if (window.currentBotMode === "Assist") {{
                fetchAndDisplayMove(false);
            }} else if (window.currentBotMode === "Auto-Play") {{
                const fen = getFEN();
                if (fen.split(' ')[1] === getMyColor()) fetchAndDisplayMove(true);
            }}
        }});
        document.body.appendChild(btn);
        
        document.addEventListener('keydown', (event) => {{
            if (event.shiftKey && event.code === 'Space') {{
                event.preventDefault();
                const fen = getFEN();
                if (fen.split(' ')[1] === getMyColor()) {{
                    fetchAndDisplayMove(window.currentBotMode === "Auto-Play");
                }} else {{
                    fetchAndDisplayMove(false);
                }}
            }}
        }});
        
        window.nemesis = {{
            forceMove: () => fetchAndDisplayMove(window.currentBotMode === "Auto-Play"),
            highlight: () => fetchAndDisplayMove(false),
            setMode: (mode) => {{
                window.currentBotMode = mode;
                window.botActive = (mode === "Auto-Play");
                if (mode === "Auto-Play") startAutoPlay(); else stopAutoPlay();
            }}
        }};
        console.log(`[NEMESIS] Injected | Mode: ${{window.currentBotMode}} | Color: {color} | Delay: {delay}ms`);
    }})();
    """
    try:
        bot_instance.page.run_js(js_code)
        return jsonify({"message": f"NEMESIS payload injected. Mode: {play_mode}"})
    except Exception as e:
        return jsonify({"message": f"Injection failed: {str(e)}"}), 500


def start_flask():
    import logging

    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=5000, use_reloader=False)


if __name__ == "__main__":
    if not os.path.exists(ACC_FILE):
        save_json(ACC_FILE, {"username": "YourUsername", "pass": "YourPassword"})
    threading.Thread(target=start_flask, daemon=True).start()
    sleep(1)
    window = webview.create_window(
        "Chess cheat",
        "http://127.0.0.1:5000",
        width=950,
        height=650,
        background_color="#070303",
        frameless=False,
    )
    window.events.closed += force_cleanup
    webview.start()
