import { supabase } from "../supabaseClient";
import { useEffect, useState, useRef } from "react";
import Head from "next/head";

export default function Gallery() {
    const [photos, setPhotos] = useState([]);
    const [commandChannel, setCommandChannel] = useState(null);
    const [activeMode, setActiveMode] = useState('SINGLE');
    const [activeFilter, setActiveFilter] = useState(null);
    const [loading, setLoading] = useState(true);
    const [visiblePhotos, setVisiblePhotos] = useState(new Set());
    const photoRefs = useRef({});

    useEffect(() => {
        loadPhotos();

        const dbChannel = supabase
            .channel("photos-changes")
            .on("postgres_changes", { event: "INSERT", schema: "public", table: "photos" }, payload => {
                setPhotos(prev => [{ ...payload.new, isNew: true }, ...prev]);
                setTimeout(() => {
                    setPhotos(prev => prev.map(p => p.id === payload.new.id ? { ...p, isNew: false } : p));
                }, 1500);
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

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    const id = entry.target.dataset.id;
                    if (entry.isIntersecting) {
                        setVisiblePhotos(prev => new Set([...prev, id]));
                    }
                });
            },
            { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
        );

        Object.values(photoRefs.current).forEach(ref => {
            if (ref) observer.observe(ref);
        });

        return () => observer.disconnect();
    }, [photos]);

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

    const downloadPhoto = async (url, filename) => {
        try {
            const response = await fetch(url);
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename || 'mascot_photo.jpg';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(blobUrl);
        } catch (err) {
            window.open(url, '_blank');
        }
    };

    return (
        <div className="page-container">
            <Head>
                <title>MASCOT - Excel Techfest 2025</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet" />
            </Head>

            {/* Background */}
            <div className="bg-pattern"></div>

            {/* Header */}
            <header className="mascot-header">
                <h1 className="mascot-title">VISUAL LOGS</h1>
                <p className="mascot-subtitle">EXCEL TECHFEST 2025 // MASCOT_BOOTH</p>
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
                        <button className={`filter-btn ${activeFilter === 'BW' ? 'active' : ''}`} onClick={() => setFilter('BW')}>B&W</button>
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
                ) : photos.length === 0 ? (
                    <div className="empty-state">
                        <p>No photos yet. Show a thumbs up to capture!</p>
                    </div>
                ) : (
                    <div className="timeline-track">
                        {/* Main vertical line */}
                        <div className="main-line"></div>
                        
                        {photos.map((photo, index) => {
                            const isLeft = index % 2 === 0;
                            return (
                                <div 
                                    key={photo.id} 
                                    className={`photo-node ${visiblePhotos.has(photo.id.toString()) ? 'visible' : ''} ${photo.isNew ? 'new-photo' : ''} ${isLeft ? 'left' : 'right'}`}
                                    ref={el => photoRefs.current[photo.id] = el}
                                    data-id={photo.id}
                                >
                                    {/* Branch connector - curves from center line to photo top */}
                                    <svg className="branch-connector" viewBox="0 0 200 120" preserveAspectRatio="none">
                                        <path 
                                            className="branch-path" 
                                            d={isLeft 
                                                ? "M200,60 C150,60 150,10 100,10 L0,10" 
                                                : "M0,60 C50,60 50,10 100,10 L200,10"
                                            } 
                                        />
                                        <circle className="branch-dot-center" cx={isLeft ? "200" : "0"} cy="60" r="6" />
                                        <circle className="branch-dot-end" cx={isLeft ? "0" : "200"} cy="10" r="4" />
                                    </svg>
                                    
                                    {/* Polaroid card */}
                                    <div className="polaroid-card">
                                        <div className="tape"></div>
                                        <div className="photo-frame">
                                            <img src={photo.image_url} alt="Memory" loading="lazy" />
                                        </div>
                                        <div className="photo-info">
                                            <p className="rec-date">REC_DATE: {formatDate(photo.created_at)}</p>
                                            <p className="location">LOC: College Ground</p>
                                        </div>
                                        <div className="photo-footer">
                                            <span className="photo-id">EXCEL_LOG_{String(index + 1).padStart(2, '0')}</span>
                                            <span className="excel-badge">[EXCELETED]</span>
                                        </div>
                                        <button 
                                            className="download-btn"
                                            onClick={() => downloadPhoto(photo.image_url, `excel_photo_${photo.id}.jpg`)}
                                        >
                                            ↓ DOWNLOAD
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="main-footer">
                <p>EXCEL TECHFEST 2025 // MASCOT_BOOTH_V2.1</p>
            </footer>

            <style jsx global>{`
                :root {
                    --bg-dark: #0a0a0a;
                    --bg-darker: #050505;
                    --gold: #D4A84B;
                    --gold-bright: #F5C842;
                    --orange: #E8943A;
                    --cream: #f5f0e6;
                    --text: #e0e0e0;
                    --text-dim: #666;
                    --border: #2a2a2a;
                }

                * { box-sizing: border-box; margin: 0; padding: 0; }

                body {
                    background: var(--bg-darker);
                    color: var(--text);
                    font-family: 'Share Tech Mono', monospace;
                    min-height: 100vh;
                    overflow-x: hidden;
                }

                .page-container {
                    position: relative;
                    min-height: 100vh;
                }

                /* Vintage photobooth background pattern */
                .bg-pattern {
                    position: fixed;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background: 
                        radial-gradient(ellipse at 20% 20%, rgba(212, 168, 75, 0.08) 0%, transparent 40%),
                        radial-gradient(ellipse at 80% 80%, rgba(232, 148, 58, 0.06) 0%, transparent 40%),
                        radial-gradient(ellipse at 50% 50%, rgba(20, 20, 20, 1) 0%, rgba(5, 5, 5, 1) 100%);
                    z-index: -2;
                }

                .bg-pattern::before {
                    content: '';
                    position: absolute;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background-image: 
                        repeating-linear-gradient(
                            0deg,
                            transparent,
                            transparent 2px,
                            rgba(255, 255, 255, 0.01) 2px,
                            rgba(255, 255, 255, 0.01) 4px
                        );
                    pointer-events: none;
                }

                .bg-pattern::after {
                    content: '';
                    position: absolute;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background: 
                        radial-gradient(circle at 50% 0%, rgba(212, 168, 75, 0.1) 0%, transparent 30%);
                    pointer-events: none;
                }

                /* Header */
                .mascot-header {
                    text-align: center;
                    padding: 50px 20px 30px;
                    position: relative;
                }

                .mascot-title {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 2.8rem;
                    font-weight: 700;
                    color: var(--gold);
                    letter-spacing: 8px;
                    text-shadow: 
                        0 0 40px rgba(212, 168, 75, 0.4),
                        0 2px 0 rgba(0, 0, 0, 0.3);
                    margin-bottom: 10px;
                }

                .mascot-subtitle {
                    font-size: 0.75rem;
                    color: var(--text-dim);
                    letter-spacing: 4px;
                }

                /* Controls Panel */
                .controls-panel {
                    max-width: 800px;
                    margin: 0 auto 50px;
                    padding: 20px 25px;
                    background: rgba(15, 15, 15, 0.9);
                    border: 1px solid var(--border);
                    border-left: 3px solid var(--gold);
                }

                .panel-section {
                    margin-bottom: 15px;
                }

                .panel-section:last-child {
                    margin-bottom: 0;
                }

                .panel-label {
                    color: var(--text-dim);
                    font-size: 0.65rem;
                    margin-bottom: 10px;
                    letter-spacing: 1px;
                }

                .filter-buttons, .mode-buttons {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    justify-content: center;
                }

                .filter-btn {
                    background: transparent;
                    border: 1px solid var(--border);
                    color: #888;
                    padding: 8px 16px;
                    font-family: 'Share Tech Mono', monospace;
                    font-size: 0.75rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }

                .filter-btn:hover {
                    border-color: var(--gold);
                    color: var(--gold);
                }

                .filter-btn.active {
                    background: var(--gold);
                    color: #000;
                    border-color: var(--gold);
                    box-shadow: 0 0 15px rgba(212, 168, 75, 0.4);
                }

                .mode-btn {
                    background: transparent;
                    border: 1px solid var(--border);
                    color: #666;
                    padding: 8px 14px;
                    font-family: 'Orbitron', sans-serif;
                    font-size: 0.7rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }

                .mode-btn:hover {
                    color: #fff;
                    border-color: #fff;
                }

                .mode-btn.active {
                    background: var(--gold);
                    color: #000;
                    border-color: var(--gold);
                    box-shadow: 0 0 15px rgba(212, 168, 75, 0.4);
                }

                /* Timeline */
                .timeline-container {
                    max-width: 1100px;
                    margin: 0 auto;
                    padding: 0 20px 100px;
                    position: relative;
                }

                .timeline-track {
                    position: relative;
                    padding-top: 40px;
                }

                /* Main vertical line */
                .main-line {
                    position: absolute;
                    left: 50%;
                    top: 0;
                    bottom: 0;
                    width: 3px;
                    background: linear-gradient(180deg, 
                        var(--gold) 0%, 
                        var(--orange) 30%,
                        var(--gold) 60%,
                        var(--orange) 100%
                    );
                    transform: translateX(-50%);
                    box-shadow: 
                        0 0 20px rgba(212, 168, 75, 0.5),
                        0 0 40px rgba(212, 168, 75, 0.2);
                    z-index: 1;
                }

                /* Photo Node */
                .photo-node {
                    position: relative;
                    margin-bottom: 120px;
                    display: flex;
                    align-items: flex-start;
                    padding-top: 40px;
                }

                .photo-node.left {
                    justify-content: flex-start;
                    padding-right: calc(50% + 30px);
                }

                .photo-node.right {
                    justify-content: flex-end;
                    padding-left: calc(50% + 30px);
                }

                /* Branch connector SVG */
                .branch-connector {
                    position: absolute;
                    top: 0;
                    width: 50%;
                    height: 120px;
                    z-index: 2;
                    overflow: visible;
                }

                .photo-node.left .branch-connector {
                    right: 0;
                }

                .photo-node.right .branch-connector {
                    left: 0;
                }

                .branch-path {
                    fill: none;
                    stroke: #333;
                    stroke-width: 3;
                    stroke-linecap: round;
                    stroke-dasharray: 300;
                    stroke-dashoffset: 300;
                    transition: stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1), stroke 0.5s ease;
                }

                .photo-node.visible .branch-path {
                    stroke-dashoffset: 0;
                    stroke: var(--gold);
                    filter: drop-shadow(0 0 6px rgba(212, 168, 75, 0.6));
                }

                .branch-dot-center {
                    fill: #222;
                    stroke: #444;
                    stroke-width: 2;
                    transition: all 0.4s ease 0.8s;
                }

                .photo-node.visible .branch-dot-center {
                    fill: var(--gold);
                    stroke: var(--gold-bright);
                    filter: drop-shadow(0 0 8px rgba(212, 168, 75, 0.8));
                }

                .branch-dot-end {
                    fill: #222;
                    stroke: #444;
                    stroke-width: 2;
                    opacity: 0;
                    transition: all 0.3s ease 1s;
                }

                .photo-node.visible .branch-dot-end {
                    opacity: 1;
                    fill: var(--gold);
                    stroke: var(--gold-bright);
                }

                /* Polaroid Card */
                .polaroid-card {
                    background: var(--cream);
                    padding: 12px 12px 15px 12px;
                    box-shadow: 
                        0 8px 30px rgba(0, 0, 0, 0.5),
                        0 2px 10px rgba(0, 0, 0, 0.3),
                        inset 0 0 0 1px rgba(255, 255, 255, 0.1);
                    position: relative;
                    max-width: 260px;
                    transform: rotate(-2deg);
                    opacity: 0;
                    transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                    z-index: 3;
                }

                .photo-node.right .polaroid-card {
                    transform: rotate(2deg);
                }

                .photo-node.visible .polaroid-card {
                    opacity: 1;
                }

                .photo-node.new-photo .polaroid-card {
                    animation: slideIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
                }

                .polaroid-card:hover {
                    transform: rotate(0deg) scale(1.05) translateY(-5px);
                    box-shadow: 
                        0 20px 50px rgba(0, 0, 0, 0.6),
                        0 0 30px rgba(212, 168, 75, 0.2);
                    z-index: 20;
                }

                /* Tape decoration */
                .tape {
                    position: absolute;
                    top: -12px;
                    left: 50%;
                    transform: translateX(-50%) rotate(-2deg);
                    width: 60px;
                    height: 24px;
                    background: linear-gradient(135deg, 
                        rgba(212, 168, 75, 0.9) 0%, 
                        rgba(245, 200, 66, 0.8) 50%,
                        rgba(212, 168, 75, 0.9) 100%
                    );
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                    z-index: 10;
                }

                .tape::before {
                    content: '';
                    position: absolute;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background: repeating-linear-gradient(
                        90deg,
                        transparent,
                        transparent 3px,
                        rgba(255, 255, 255, 0.1) 3px,
                        rgba(255, 255, 255, 0.1) 6px
                    );
                }

                .photo-frame {
                    background: #111;
                    aspect-ratio: 1;
                    overflow: hidden;
                    margin-bottom: 10px;
                    border: 1px solid #ddd;
                }

                .photo-frame img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                    filter: grayscale(100%) sepia(20%) contrast(1.1);
                    transition: filter 0.5s ease;
                }

                .polaroid-card:hover .photo-frame img {
                    filter: grayscale(0%) sepia(0%) contrast(1.05);
                }

                .photo-info {
                    font-family: 'Share Tech Mono', monospace;
                    color: #444;
                    font-size: 0.65rem;
                    margin-bottom: 6px;
                }

                .rec-date, .location {
                    margin: 2px 0;
                }

                .photo-footer {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 0.6rem;
                    color: #666;
                    margin-bottom: 8px;
                }

                .download-btn {
                    width: 100%;
                    background: #333;
                    color: #ccc;
                    border: none;
                    padding: 8px;
                    font-family: 'Share Tech Mono', monospace;
                    font-size: 0.65rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    letter-spacing: 1px;
                }

                .download-btn:hover {
                    background: var(--gold);
                    color: #000;
                }

                /* Loading & Empty */
                .loading-spinner, .empty-state {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 100px 20px;
                    color: var(--text-dim);
                    text-align: center;
                }

                .spinner {
                    width: 40px;
                    height: 40px;
                    border: 2px solid var(--border);
                    border-top-color: var(--gold);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 15px;
                }

                /* Footer */
                .main-footer {
                    text-align: center;
                    padding: 30px;
                    color: #444;
                    font-size: 0.6rem;
                    letter-spacing: 2px;
                    border-top: 1px solid var(--border);
                }

                /* Animations */
                @keyframes slideIn {
                    0% {
                        opacity: 0;
                        transform: translateY(-30px) rotate(-5deg) scale(0.9);
                    }
                    100% {
                        opacity: 1;
                        transform: translateY(0) rotate(-2deg) scale(1);
                    }
                }

                @keyframes spin {
                    to { transform: rotate(360deg); }
                }

                /* Responsive */
                @media (max-width: 768px) {
                    .mascot-title {
                        font-size: 1.8rem;
                        letter-spacing: 4px;
                    }

                    .photo-node.left,
                    .photo-node.right {
                        padding-left: 50px;
                        padding-right: 15px;
                        justify-content: flex-start;
                    }

                    .main-line {
                        left: 20px;
                    }

                    .branch-connector {
                        display: none;
                    }

                    .polaroid-card,
                    .photo-node.right .polaroid-card {
                        transform: rotate(-1deg);
                        max-width: 220px;
                    }

                    .polaroid-card:hover {
                        transform: rotate(0deg) scale(1.03);
                    }

                    .controls-panel {
                        margin: 0 10px 40px;
                        padding: 15px;
                    }

                    .filter-btn, .mode-btn {
                        padding: 6px 10px;
                        font-size: 0.65rem;
                    }

                    .photo-node {
                        margin-bottom: 80px;
                    }
                }
            `}</style>
        </div>
    );
}
