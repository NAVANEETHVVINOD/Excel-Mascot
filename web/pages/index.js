import { supabase } from "../supabaseClient";
import { useEffect, useState } from "react";
import Head from "next/head";

export default function Gallery() {
    const [photos, setPhotos] = useState([]);
    const [commandChannel, setCommandChannel] = useState(null);

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

    return (
        <div className="container">
            <Head>
                <title>Mascot Memories</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Rock+Salt&display=swap" rel="stylesheet" />
            </Head>

            <div className="noise-overlay"></div>

            <header>
                <div className="badge">Excel 2025</div>
                <h1>MASCOT BOOTH</h1>
                <p className="subtitle">Capture the Vibe ✨</p>
            </header>

            <section className="controls-section">
                <div className="tape-label">REMOTE CONTROL</div>
                <div className="control-group">
                    <button className="retro-btn glitch" onClick={() => sendCommand('SET_FILTER', { filter: 'GLITCH' })}>GLITCH</button>
                    <button className="retro-btn cyber" onClick={() => sendCommand('SET_FILTER', { filter: 'CYBERPUNK' })}>NEON</button>
                    <button className="retro-btn pastel" onClick={() => sendCommand('SET_FILTER', { filter: 'PASTEL' })}>DREAMY</button>
                    <button className="retro-btn polaroid" onClick={() => sendCommand('SET_FILTER', { filter: 'POLAROID' })}>CLASSIC</button>
                    <button className="retro-btn bw" onClick={() => sendCommand('SET_FILTER', { filter: 'BW' })}>NOIR</button>
                    <button className="retro-btn reset" onClick={() => sendCommand('SET_FILTER', { filter: 'NONE' })}>RESET</button>
                </div>
                <div className="control-group small-gap">
                    <button className="sm-btn" onClick={() => sendCommand('SET_MODE', { mode: 'BURST' })}>💥 BURST</button>
                    <button className="sm-btn" onClick={() => sendCommand('SET_MODE', { mode: 'GIF' })}>🎥 GIF</button>
                    <button className="sm-btn" onClick={() => sendCommand('SET_MODE', { mode: 'SINGLE' })}>📸 1 SHOT</button>
                </div>
            </section>

            <main className="gallery">
                {photos.map((p, index) => (
                    <div key={p.id} className={`polaroid-card delay-${index % 5}`}>
                        <div className="tape"></div>
                        <div className="image-frame">
                            <img src={p.image_url} alt="Memory" loading="lazy" />
                        </div>
                        <div className="handwritten">Mascot '25</div>
                        <div className="card-actions">
                            <a href={p.image_url} download className="save-link">SAVE</a>
                        </div>
                    </div>
                ))}
            </main>

            <footer>
                <p>Made with ❤️ for Excel 2025</p>
            </footer>

            <style jsx global>{`
                :root {
                    --bg: #2b2b2b;
                    --paper: #f4f1ea;
                    --tape: rgba(255, 255, 255, 0.4);
                    --accent: #ff0055;
                }

                * { box-sizing: border-box; }

                body {
                    margin: 0;
                    background-color: #222;
                    background-image: 
                        linear-gradient(45deg, #1a1a1a 25%, transparent 25%, transparent 75%, #1a1a1a 75%, #1a1a1a), 
                        linear-gradient(45deg, #1a1a1a 25%, transparent 25%, transparent 75%, #1a1a1a 75%, #1a1a1a);
                    background-size: 40px 40px;
                    background-position: 0 0, 20px 20px;
                    color: white;
                    font-family: 'Permanent Marker', cursive;
                    min-height: 100vh;
                    overflow-x: hidden;
                }

                /* Noise Texture */
                .noise-overlay {
                    position: fixed; top:0; left:0; width:100%; height:100%;
                    background: url('https://grainy-gradients.vercel.app/noise.svg');
                    opacity: 0.05;
                    pointer-events: none;
                    z-index: 999;
                }

                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 20px;
                }

                header {
                    text-align: center;
                    margin-bottom: 40px;
                    position: relative;
                }

                .badge {
                    display: inline-block;
                    background: var(--accent);
                    padding: 5px 15px;
                    transform: rotate(-3deg);
                    font-size: 1.2rem;
                    box-shadow: 3px 3px 0 rgba(0,0,0,0.5);
                    margin-bottom: 10px;
                }

                h1 {
                    font-family: 'Rock Salt', cursive;
                    font-size: 3rem;
                    margin: 10px 0;
                    text-shadow: 4px 4px 0 #000;
                    color: #fff;
                    letter-spacing: 2px;
                }
                
                @media (max-width: 600px) {
                    h1 { font-size: 2rem; }
                }

                .subtitle {
                    color: #aaa;
                    font-family: sans-serif;
                    letter-spacing: 3px;
                    text-transform: uppercase;
                    font-size: 0.9rem;
                }

                /* Controls */
                .controls-section {
                    background: rgba(255,255,255,0.05);
                    border: 2px dashed rgba(255,255,255,0.2);
                    padding: 20px;
                    margin-bottom: 50px;
                    border-radius: 10px;
                    position: relative;
                    text-align: center;
                }

                .tape-label {
                    position: absolute;
                    top: -15px;
                    left: 50%;
                    transform: translateX(-50%) rotate(-1deg);
                    background: #ffeb3b;
                    color: black;
                    padding: 5px 20px;
                    font-size: 1rem;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
                }

                .control-group {
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                    gap: 15px;
                    margin-top: 15px;
                }
                .small-gap { margin-top: 20px; gap: 10px; }

                .retro-btn {
                    font-family: 'Permanent Marker', cursive;
                    border: none;
                    padding: 12px 20px;
                    font-size: 1rem;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.2s;
                    box-shadow: 4px 4px 0 #000;
                    text-transform: uppercase;
                }
                
                .retro-btn:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0 #000; }
                .retro-btn:active { transform: translate(2px, 2px); box-shadow: 2px 2px 0 #000; }

                .glitch { background: #0ff; color: #000; }
                .cyber { background: #f0f; color: #fff; }
                .pastel { background: #ffd1fb; color: #000; }
                .polaroid { background: #fff; color: #000; }
                .bw { background: #888; color: #fff; }
                .reset { background: #333; color: #fff; border: 1px solid #555; }

                .sm-btn {
                    background: transparent;
                    border: 2px solid #fff;
                    color: #fff;
                    padding: 8px 15px;
                    cursor: pointer;
                    font-family: sans-serif;
                    font-weight: bold;
                    border-radius: 20px;
                    transition: 0.2s;
                    font-size: 0.8rem;
                }
                .sm-btn:hover { background: #fff; color: #000; }

                /* Gallery Grid */
                .gallery {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                    gap: 40px;
                    padding: 20px;
                }

                /* Polaroid Card */
                .polaroid-card {
                    background: white;
                    padding: 15px 15px 60px 15px;
                    box-shadow: 10px 10px 15px rgba(0,0,0,0.5);
                    transform: rotate(var(--rot));
                    transition: transform 0.3s, z-index 0s;
                    position: relative;
                    animation: fadeUp 0.6s ease-out forwards;
                    opacity: 0;
                }
                
                .polaroid-card:nth-child(odd) { --rot: -2deg; }
                .polaroid-card:nth-child(even) { --rot: 2deg; }
                .polaroid-card:nth-child(3n) { --rot: 1deg; }

                .polaroid-card:hover {
                    transform: scale(1.05) rotate(0deg);
                    z-index: 10;
                    box-shadow: 20px 20px 30px rgba(0,0,0,0.7);
                }

                .image-frame {
                    background: #eee;
                    width: 100%;
                    aspect-ratio: 1; /* Square crop suggestion or auto */
                    overflow: hidden;
                    border: 1px solid #ddd;
                }
                
                .image-frame img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                    filter: contrast(1.1) brightness(1.1);
                }

                .tape {
                    position: absolute;
                    top: -15px;
                    left: 50%;
                    transform: translateX(-50%) rotate(2deg);
                    width: 100px;
                    height: 30px;
                    background-color: rgba(255, 255, 255, 0.3);
                    backdrop-filter: blur(2px);
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    border: 1px solid rgba(255,255,255,0.4);
                }

                .handwritten {
                    position: absolute;
                    bottom: 25px;
                    left: 0;
                    width: 100%;
                    text-align: center;
                    color: #444;
                    font-size: 1.2rem;
                    font-family: 'Permanent Marker', cursive;
                    transform: rotate(-1deg);
                }

                .card-actions {
                    position: absolute;
                    bottom: 5px;
                    right: 10px;
                }

                .save-link {
                    text-decoration: none;
                    font-family: sans-serif;
                    font-size: 0.7rem;
                    color: #999;
                    text-transform: uppercase;
                    border: 1px solid #ddd;
                    padding: 2px 5px;
                    border-radius: 4px;
                }
                .save-link:hover { background: #eee; color: #333; }

                /* Animations */
                @keyframes fadeUp {
                    from { transform: translateY(50px) rotate(0); opacity: 0; }
                    to { opacity: 1; }
                }
                
                .delay-0 { animation-delay: 0.1s; }
                .delay-1 { animation-delay: 0.2s; }
                .delay-2 { animation-delay: 0.3s; }
                .delay-3 { animation-delay: 0.4s; }
                .delay-4 { animation-delay: 0.5s; }

                footer {
                    text-align: center;
                    margin-top: 50px;
                    color: #666;
                    font-family: sans-serif;
                    font-size: 0.8rem;
                }
            `}</style>
        </div>
    );
}
