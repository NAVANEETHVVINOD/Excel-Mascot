import { supabase } from "../supabaseClient";
import { useEffect, useState } from "react";
import Head from "next/head";

export default function Gallery() {
    const [photos, setPhotos] = useState([]);
    const [commandChannel, setCommandChannel] = useState(null);
    const [activeMode, setActiveMode] = useState('SINGLE');
    const [activeFilter, setActiveFilter] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadPhotos();

        const dbChannel = supabase
            .channel("photos-changes")
            .on("postgres_changes", { event: "INSERT", schema: "public", table: "photos" }, payload => {
                setPhotos(prev => [{ ...payload.new, isNew: true }, ...prev]);
                setTimeout(() => {
                    setPhotos(prev => prev.map(p => p.id === payload.new.id ? { ...p, isNew: false } : p));
                }, 1000);
            })
            .subscribe();

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
        setLoading(true);
        try {
            let { data, error } = await supabase
                .from("photos")
                .select("*")
                .order("created_at", { ascending: false });
            if (error) {
                console.error("Error loading photos:", error);
            } else {
                setPhotos(data || []);
            }
        } catch (err) {
            console.error("Failed to load photos:", err);
        }
        setLoading(false);
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

    const setFilter = (filter) => {
        if (activeFilter === filter) {
            setActiveFilter(null);
            sendCommand('SET_FILTER', { filter: 'NONE' });
        } else {
            setActiveFilter(filter);
            sendCommand('SET_FILTER', { filter });
        }
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.getFullYear();
    };

    return (
        <div className="page-container">
            <Head>
                <title>Excel Mascot Booth 2025</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet" />
            </Head>

            {/* Background */}
            <div className="bg-overlay"></div>

            {/* Header */}
            <header className="main-header">
                <div className="logo">
                    <span className="logo-icon">✕</span>
                    <span className="logo-text">EXCEL 2025</span>
                </div>
                <nav className="main-nav">
                    <a href="#" className="nav-link active">HOME</a>
                    <a href="#" className="nav-link">COMPETITIONS</a>
                    <a href="#" className="nav-link">EVENTS</a>
                    <a href="#" className="nav-link">SCHEDULE</a>
                    <a href="#" className="nav-link">CONTACT</a>
                    <a href="#" className="nav-link login">→ LOGIN</a>
                </nav>
            </header>

            {/* Controls Panel */}
            <section className="controls-panel">
                <div className="panel-section">
                    <div className="panel-label">/// FILTERS_MODULE</div>
                    <div className="filter-buttons">
                        <button className={`filter-btn ${activeFilter === 'GLITCH' ? 'active' : ''}`} onClick={() => setFilter('GLITCH')}>GLITCH</button>
                        <button className={`filter-btn ${activeFilter === 'NEON' ? 'active' : ''}`} onClick={() => setFilter('NEON')}>NEON</button>
                        <button className={`filter-btn ${activeFilter === 'DREAMY' ? 'active' : ''}`} onClick={() => setFilter('DREAMY')}>DREAMY</button>
                        <button className={`filter-btn ${activeFilter === 'RETRO' ? 'active' : ''}`} onClick={() => setFilter('RETRO')}>RETRO</button>
                        <button className={`filter-btn ${activeFilter === 'NOIR' ? 'active' : ''}`} onClick={() => setFilter('NOIR')}>NOIR</button>
                    </div>
                </div>
                <div className="panel-section">
                    <div className="panel-label">/// CAPTURE_MODE</div>
                    <div className="mode-buttons">
                        <button className={`mode-btn ${activeMode === 'BURST' ? 'active' : ''}`} onClick={() => setMode('BURST')}>[ BURST ]</button>
                        <button className={`mode-btn ${activeMode === 'GIF' ? 'active' : ''}`} onClick={() => setMode('GIF')}>[ GIF ]</button>
                        <button className={`mode-btn ${activeMode === 'SINGLE' ? 'active' : ''}`} onClick={() => setMode('SINGLE')}>[ SINGLE ]</button>
                    </div>
                </div>
            </section>

            {/* Timeline Gallery */}
            <main className="timeline-container">
                {loading ? (
                    <div className="loading-spinner">
                        <div className="spinner"></div>
                        <p>Loading memories...</p>
                    </div>
                ) : (
                    <>
                        <div className="timeline-line"></div>
                        {photos.map((photo, index) => (
                            <div key={photo.id} className={`polaroid-wrapper ${photo.isNew ? 'new-photo' : ''}`}>
                                <div className="timeline-dot"></div>
                                <div className="polaroid-card">
                                    <div className="pin"></div>
                                    <div className="photo-frame">
                                        <img src={photo.image_url} alt="Memory" loading="lazy" />
                                    </div>
                                    <div className="photo-info">
                                        <p className="rec-date">REC_DATE: {formatDate(photo.created_at)}</p>
                                        <p className="location">LOC: College Ground</p>
                                    </div>
                                    <div className="badge-container">
                                        <span className="excel-badge">[EXCELETED]</span>
                                    </div>
                                    <a href={photo.image_url} download target="_blank" className="download-link">
                                        ↓ DOWNLOAD
                                    </a>
                                </div>
                            </div>
                        ))}
                    </>
                )}
            </main>

            {/* Footer */}
            <footer className="main-footer">
                <p>EXCEL TECHFEST 2025 // MASCOT_BOOTH_V2.1</p>
            </footer>

            <style jsx global>{`
                :root {
                    --bg-dark: #0a0a0a;
                    --bg-card: #1a1a1a;
                    --gold: #FFD700;
                    --orange: #FF8C00;
                    --cyan: #00f3ff;
                    --text: #e0e0e0;
                    --text-dim: #666;
                    --border: #333;
                }

                * { box-sizing: border-box; margin: 0; padding: 0; }

                body {
                    background: var(--bg-dark);
                    color: var(--text);
                    font-family: 'Share Tech Mono', monospace;
                    min-height: 100vh;
                    overflow-x: hidden;
                }

                .page-container {
                    position: relative;
                    min-height: 100vh;
                }

                .bg-overlay {
                    position: fixed;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background: 
                        radial-gradient(ellipse at 20% 50%, rgba(255, 140, 0, 0.05) 0%, transparent 50%),
                        radial-gradient(ellipse at 80% 50%, rgba(255, 215, 0, 0.03) 0%, transparent 50%),
                        linear-gradient(180deg, #050505 0%, #0a0a0a 100%);
                    z-index: -1;
                }

                /* Header */
                .main-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 15px 40px;
                    border-bottom: 1px solid var(--border);
                    background: rgba(10, 10, 10, 0.9);
                    backdrop-filter: blur(10px);
                    position: sticky;
                    top: 0;
                    z-index: 100;
                }

                .logo {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .logo-icon {
                    color: var(--gold);
                    font-size: 2rem;
                    font-weight: bold;
                }

                .logo-text {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 1.2rem;
                    color: var(--gold);
                    letter-spacing: 2px;
                }

                .main-nav {
                    display: flex;
                    gap: 30px;
                    align-items: center;
                }

                .nav-link {
                    color: var(--text-dim);
                    text-decoration: none;
                    font-size: 0.85rem;
                    letter-spacing: 1px;
                    transition: color 0.3s;
                }

                .nav-link:hover, .nav-link.active {
                    color: var(--gold);
                }

                .nav-link.login {
                    color: var(--text);
                    border: 1px solid var(--border);
                    padding: 5px 15px;
                }

                /* Controls Panel */
                .controls-panel {
                    max-width: 1200px;
                    margin: 30px auto;
                    padding: 20px;
                    background: rgba(20, 20, 20, 0.8);
                    border: 1px solid var(--border);
                    border-left: 4px solid var(--gold);
                }

                .panel-section {
                    margin-bottom: 20px;
                }

                .panel-section:last-child {
                    margin-bottom: 0;
                }

                .panel-label {
                    color: var(--text-dim);
                    font-size: 0.75rem;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #222;
                    display: inline-block;
                    padding-right: 20px;
                }

                .filter-buttons, .mode-buttons {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                    justify-content: center;
                }

                .filter-btn {
                    background: transparent;
                    border: 1px solid var(--border);
                    color: var(--text);
                    padding: 10px 20px;
                    font-family: 'Share Tech Mono', monospace;
                    cursor: pointer;
                    transition: all 0.2s;
                    text-transform: uppercase;
                }

                .filter-btn:hover {
                    border-color: var(--gold);
                    color: var(--gold);
                    box-shadow: 0 0 10px rgba(255, 215, 0, 0.2);
                }

                .filter-btn.active {
                    background: var(--gold);
                    color: #000;
                    border-color: var(--gold);
                    box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
                    font-weight: bold;
                }

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

                .mode-btn:hover {
                    color: white;
                    border-color: white;
                }

                .mode-btn.active {
                    background: var(--gold);
                    color: black;
                    border-color: var(--gold);
                    box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
                    font-weight: bold;
                }
</div>

                /* Timeline Gallery */
                .timeline-container {
                    max-width: 800px;
                    margin: 40px auto;
                    padding: 20px;
                    position: relative;
                    min-height: 400px;
                }

                .timeline-line {
                    position: absolute;
                    left: 50%;
                    top: 0;
                    bottom: 0;
                    width: 3px;
                    background: linear-gradient(180deg, var(--gold) 0%, var(--orange) 100%);
                    transform: translateX(-50%);
                    z-index: 1;
                }

                .polaroid-wrapper {
                    position: relative;
                    margin-bottom: 60px;
                    display: flex;
                    justify-content: center;
                    animation: fadeInUp 0.5s ease-out;
                }

                .polaroid-wrapper.new-photo {
                    animation: popIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                }

                .timeline-dot {
                    position: absolute;
                    left: 50%;
                    top: 50%;
                    width: 16px;
                    height: 16px;
                    background: var(--gold);
                    border: 3px solid var(--bg-dark);
                    border-radius: 50%;
                    transform: translate(-50%, -50%);
                    z-index: 2;
                    box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
                }

                .polaroid-card {
                    background: #f5f5f0;
                    padding: 15px 15px 20px 15px;
                    box-shadow: 
                        0 4px 20px rgba(0, 0, 0, 0.5),
                        0 0 0 1px rgba(255, 255, 255, 0.1);
                    position: relative;
                    transform: rotate(-2deg);
                    transition: transform 0.3s, box-shadow 0.3s;
                    max-width: 320px;
                    margin-left: 80px;
                }

                .polaroid-wrapper:nth-child(even) .polaroid-card {
                    transform: rotate(2deg);
                    margin-left: 0;
                    margin-right: 80px;
                }

                .polaroid-card:hover {
                    transform: rotate(0deg) scale(1.02);
                    box-shadow: 
                        0 8px 30px rgba(0, 0, 0, 0.6),
                        0 0 20px rgba(255, 215, 0, 0.2);
                }

                .pin {
                    position: absolute;
                    top: -8px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 20px;
                    height: 20px;
                    background: radial-gradient(circle at 30% 30%, #ffd700, #b8860b);
                    border-radius: 50%;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
                    z-index: 10;
                }

                .pin::after {
                    content: '';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    width: 6px;
                    height: 6px;
                    background: rgba(255, 255, 255, 0.6);
                    border-radius: 50%;
                    transform: translate(-50%, -50%);
                }

                .photo-frame {
                    background: #000;
                    aspect-ratio: 1;
                    overflow: hidden;
                    margin-bottom: 15px;
                }

                .photo-frame img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                    filter: contrast(1.05);
                }

                .photo-info {
                    font-family: 'Share Tech Mono', monospace;
                    color: #333;
                    font-size: 0.8rem;
                    margin-bottom: 10px;
                }

                .rec-date, .location {
                    margin: 3px 0;
                }

                .badge-container {
                    text-align: right;
                    margin-bottom: 10px;
                }

                .excel-badge {
                    font-family: 'Share Tech Mono', monospace;
                    font-size: 0.7rem;
                    color: #666;
                    letter-spacing: 1px;
                }

                .download-link {
                    display: block;
                    text-align: center;
                    background: #222;
                    color: #fff;
                    padding: 8px;
                    text-decoration: none;
                    font-size: 0.75rem;
                    letter-spacing: 1px;
                    transition: background 0.2s;
                }

                .download-link:hover {
                    background: var(--gold);
                    color: #000;
                }

                /* Loading */
                .loading-spinner {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 60px;
                    color: var(--text-dim);
                }

                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 3px solid var(--border);
                    border-top-color: var(--gold);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 15px;
                }

                /* Footer */
                .main-footer {
                    text-align: center;
                    padding: 30px;
                    color: var(--text-dim);
                    font-size: 0.7rem;
                    border-top: 1px solid var(--border);
                    margin-top: 60px;
                }

                /* Animations */
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(30px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes popIn {
                    0% {
                        opacity: 0;
                        transform: scale(0.5);
                    }
                    70% {
                        transform: scale(1.1);
                    }
                    100% {
                        opacity: 1;
                        transform: scale(1);
                    }
                }

                @keyframes spin {
                    to { transform: rotate(360deg); }
                }

                /* Responsive */
                @media (max-width: 768px) {
                    .main-header {
                        flex-direction: column;
                        gap: 15px;
                        padding: 15px;
                    }

                    .main-nav {
                        flex-wrap: wrap;
                        justify-content: center;
                        gap: 15px;
                    }

                    .timeline-line {
                        left: 30px;
                    }

                    .timeline-dot {
                        left: 30px;
                    }

                    .polaroid-card,
                    .polaroid-wrapper:nth-child(even) .polaroid-card {
                        margin-left: 60px;
                        margin-right: 10px;
                        max-width: 280px;
                    }

                    .controls-panel {
                        margin: 15px;
                    }
                }
            `}</style>
        </div>
    );
}
