import { supabase } from "../supabaseClient";
import { useEffect, useState } from "react";
import Head from "next/head";

export default function Gallery() {
    const [photos, setPhotos] = useState([]);
    const [commandChannel, setCommandChannel] = useState(null);
    const [activeMode, setActiveMode] = useState('SINGLE'); // Default mode state for UI feedback

    // Initial Load & Realtime
    useEffect(() => {
        loadPhotos();

        // 1. Database Subscription
        const dbChannel = supabase
            .channel("photos-changes")
            .on("postgres_changes", { event: "INSERT", schema: "public", table: "photos" }, payload => {
                setPhotos(prev => [payload.new, ...prev]);
            })
            .subscribe();

        // 2. Broadcast Channel (Remote Control)
        const cmdChannel = supabase.channel('booth_control');
        cmdChannel.subscribe(status => {
            if (status === 'SUBSCRIBED') setCommandChannel(cmdChannel);
        });

        return () => {
            supabase.removeChannel(dbChannel);
            supabase.removeChannel(cmdChannel);
        };
    }, []);

    async function loadPhotos() {
        let { data, error } = await supabase
            .from("photos")
            .select("*")
            .order("created_at", { ascending: false });
        if (!error) setPhotos(data || []);
    }

    const sendCommand = async (type, payload) => {
        if (commandChannel) {
            await commandChannel.send({
                type: 'broadcast',
                event: 'command',
                payload: { type, ...payload }
            });
        }
    };

    const setMode = (mode) => {
        setActiveMode(mode);
        sendCommand('SET_MODE', { mode });
    };

    return (
        <div className="container">
            <Head>
                <title>Mascot Memories</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet" />
            </Head>

            <div className="grid-overlay"></div>
            <div className="scanline"></div>

            <header>
                <div className="badge">EXCEL 2025</div>
                <h1>MASCOT BOOTH</h1>
                <div className="status-line">SYSTEM STATUS: <span className="blink">ONLINE</span></div>
            </header>

            <section className="controls-section">
                <div className="panel-header">/// FILTERS_MODULE</div>
                <div className="control-group">
                    <button className="tech-btn glitch-effect" onClick={() => sendCommand('SET_FILTER', { filter: 'GLITCH' })}>GLITCH</button>
                    <button className="tech-btn neon-effect" onClick={() => sendCommand('SET_FILTER', { filter: 'CYBERPUNK' })}>NEON</button>
                    <button className="tech-btn dreamy-effect" onClick={() => sendCommand('SET_FILTER', { filter: 'PASTEL' })}>DREAMY</button>
                    <button className="tech-btn retro-effect" onClick={() => sendCommand('SET_FILTER', { filter: 'POLAROID' })}>RETRO</button>
                    <button className="tech-btn bw-effect" onClick={() => sendCommand('SET_FILTER', { filter: 'BW' })}>NOIR</button>
                    <button className="tech-btn reset-effect" onClick={() => sendCommand('SET_FILTER', { filter: 'NONE' })}>RESET</button>
                </div>

                <div className="panel-spacer"></div>

                <div className="panel-header">/// CAPTURE_MODE</div>
                <div className="control-group small-gap">
                    <button className={`mode-btn ${activeMode === 'BURST' ? 'active' : ''}`} onClick={() => setMode('BURST')}>[ BURST ]</button>
                    <button className={`mode-btn ${activeMode === 'GIF' ? 'active' : ''}`} onClick={() => setMode('GIF')}>[ GIF ]</button>
                    <button className={`mode-btn ${activeMode === 'SINGLE' ? 'active' : ''}`} onClick={() => setMode('SINGLE')}>[ SINGLE ]</button>
                </div>
            </section>

            <main className="gallery">
                {photos.map((p, index) => (
                    <div key={p.id} className="tech-card">
                        <div className="card-header">
                            <span>IMG_{p.id}</span>
                            <span>{new Date(p.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <div className="image-frame">
                            <img src={p.image_url} alt="Memory" loading="lazy" />
                        </div>
                        <div className="card-footer">
                            <a href={p.image_url} download target="_blank" className="download-btn-card">
                                &darr; DOWNLOAD
                            </a>
                        </div>
                        <div className="corner-decor top-left"></div>
                        <div className="corner-decor top-right"></div>
                        <div className="corner-decor bottom-left"></div>
                        <div className="corner-decor bottom-right"></div>
                    </div>
                ))}
            </main>

            <footer>
                <p>EXCEL TECHFEST 2025 // MASCOT_SYSTEM_V2.0</p>
            </footer>

            <style jsx global>{`
                :root {
                    --bg: #050505;
                    --grid: #1a1a1a;
                    --primary: #FFD700; /* Gold */
                    --secondary: #FF8C00; /* Orange */
                    --accent: #00f3ff; /* Cyan */
                    --text: #e0e0e0;
                    --surface: #0a0a0a;
                    --border: #333;
                }

                * { box-sizing: border-box; }

                body {
                    margin: 0;
                    background-color: var(--bg);
                    color: var(--text);
                    font-family: 'Share Tech Mono', monospace;
                    min-height: 100vh;
                    overflow-x: hidden;
                }

                /* Background Effects */
                .grid-overlay {
                    position: fixed; top:0; left:0; width:100%; height:100%;
                    background-image: 
                        linear-gradient(var(--grid) 1px, transparent 1px),
                        linear-gradient(90deg, var(--grid) 1px, transparent 1px);
                    background-size: 30px 30px;
                    opacity: 0.2;
                    z-index: -1;
                    pointer-events: none;
                }
                
                .scanline {
                    position: fixed; top:0; left:0; width:100%; height:4px;
                    background: rgba(0, 243, 255, 0.1);
                    animation: scan 6s linear infinite;
                    pointer-events: none;
                    z-index: 1000;
                }

                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }

                /* Header */
                header {
                    text-align: center;
                    margin-bottom: 40px;
                    border-bottom: 2px solid var(--border);
                    padding-bottom: 20px;
                    position: relative;
                }

                .badge {
                    display: inline-block;
                    color: var(--primary);
                    border: 1px solid var(--primary);
                    padding: 2px 10px;
                    font-size: 0.8rem;
                    letter-spacing: 2px;
                    margin-bottom: 10px;
                    box-shadow: 0 0 5px rgba(255, 215, 0, 0.2);
                }

                h1 {
                    font-family: 'Orbitron', sans-serif;
                    font-weight: 900;
                    font-size: 3.5rem;
                    margin: 5px 0;
                    color: white;
                    text-transform: uppercase;
                    letter-spacing: 4px;
                    text-shadow: 2px 2px 0px var(--secondary);
                }
                
                @media (max-width: 600px) { h1 { font-size: 2rem; } }

                .status-line {
                    font-size: 0.8rem;
                    color: #666;
                    letter-spacing: 1px;
                }
                .blink { color: var(--accent); animation: blink 1s infinite; }

                /* Controls */
                .controls-section {
                    background: rgba(10, 10, 10, 0.8);
                    border: 1px solid var(--border);
                    border-left: 4px solid var(--primary);
                    padding: 20px;
                    margin-bottom: 40px;
                    backdrop-filter: blur(5px);
                }

                .panel-header {
                    color: #666;
                    font-size: 0.8rem;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #222;
                    display: inline-block;
                    padding-right: 20px;
                }
                
                .panel-spacer { height: 20px; }

                .control-group {
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                    gap: 12px;
                }

                /* Buttons */
                .tech-btn {
                    background: transparent;
                    border: 1px solid var(--border);
                    color: var(--text);
                    padding: 10px 20px;
                    font-family: 'Share Tech Mono', monospace;
                    font-size: 1rem;
                    cursor: pointer;
                    transition: all 0.2s;
                    position: relative;
                    overflow: hidden;
                    text-transform: uppercase;
                }

                .tech-btn:hover {
                    background: rgba(255, 255, 255, 0.05);
                    border-color: var(--primary);
                    color: var(--primary);
                    box-shadow: 0 0 10px rgba(255, 215, 0, 0.2);
                }
                
                .tech-btn:active { transform: scale(0.98); }

                .mode-btn {
                    background: #111;
                    border: 1px solid #333;
                    color: #888;
                    padding: 8px 16px;
                    font-family: 'Orbitron', sans-serif;
                    font-size: 0.9rem;
                    cursor: pointer;
                    transition: 0.3s;
                }
                
                .mode-btn:hover { color: white; border-color: white; }
                .mode-btn.active { 
                    background: var(--primary); 
                    color: black; 
                    border-color: var(--primary);
                    box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
                    font-weight: bold;
                }

                /* Gallery Grid */
                .gallery {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 20px;
                    padding: 10px;
                }

                /* Tech Card */
                .tech-card {
                    background: rgba(20, 20, 20, 0.9);
                    border: 1px solid #333;
                    padding: 10px;
                    position: relative;
                    transition: transform 0.3s, border-color 0.3s;
                }
                
                .tech-card:hover {
                    transform: translateY(-5px);
                    border-color: var(--accent);
                    box-shadow: 0 0 20px rgba(0, 243, 255, 0.1);
                    z-index: 10;
                }

                .card-header {
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.7rem;
                    color: #555;
                    margin-bottom: 5px;
                    font-family: 'Orbitron', sans-serif;
                }

                .image-frame {
                    background: #000;
                    border: 1px solid #222;
                    aspect-ratio: 1;
                    overflow: hidden;
                    margin-bottom: 10px;
                }
                
                .image-frame img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                    transition: transform 0.5s;
                }
                
                .tech-card:hover img { transform: scale(1.05); }

                .card-footer {
                    text-align: center;
                }

                .download-btn-card {
                    display: block;
                    width: 100%;
                    background: #111;
                    border: 1px solid #333;
                    color: white;
                    padding: 8px 0;
                    text-decoration: none;
                    text-transform: uppercase;
                    font-size: 0.8rem;
                    transition: 0.2s;
                }
                
                .download-btn-card:hover {
                    background: var(--accent);
                    color: black;
                    border-color: var(--accent);
                }

                /* Corner Decorations */
                .corner-decor {
                    position: absolute;
                    width: 6px;
                    height: 6px;
                    border: 1px solid #555;
                    transition: 0.3s;
                }
                .top-left { top: -1px; left: -1px; border-right: none; border-bottom: none; }
                .top-right { top: -1px; right: -1px; border-left: none; border-bottom: none; }
                .bottom-left { bottom: -1px; left: -1px; border-right: none; border-top: none; }
                .bottom-right { bottom: -1px; right: -1px; border-left: none; border-top: none; }
                
                .tech-card:hover .corner-decor { border-color: var(--accent); }

                /* Footer */
                footer {
                    text-align: center;
                    margin-top: 60px;
                    color: #444;
                    font-size: 0.7rem;
                    border-top: 1px solid #222;
                    padding-top: 20px;
                }

                @keyframes blink { 50% { opacity: 0; } }
                @keyframes scan { 0% { top: 0%; } 100% { top: 100%; } }

            `}</style>
        </div>
    );
}
