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

    // Intersection Observer for scroll animations
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
            { threshold: 0.15, rootMargin: '0px 0px -100px 0px' }
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
            <div className="bg-image"></div>
            <div className="bg-overlay"></div>

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
                        <div className="main-timeline-line"></div>
                        
                        {photos.map((photo, index) => (
                            <div 
                                key={photo.id} 
                                className={`photo-node ${visiblePhotos.has(photo.id.toString()) ? 'visible' : ''} ${photo.isNew ? 'new-photo' : ''} ${index % 2 === 0 ? 'left' : 'right'}`}
                                ref={el => photoRefs.current[photo.id] = el}
                                data-id={photo.id}
                            >
                                {/* Branch line from center to photo */}
                                <div className="branch-line">
                                    <svg className="branch-svg" viewBox="0 0 200 100" preserveAspectRatio="none">
                                        <path 
                                            className="branch-path" 
                                            d={index % 2 === 0 
                                                ? "M100,0 L100,50 Q100,70 80,70 L0,70" 
                                                : "M100,0 L100,50 Q100,70 120,70 L200,70"
                                            } 
                                        />
                                    </svg>
                                </div>
                                
                                {/* Timeline dot on center line */}
                                <div className="timeline-dot"></div>
                                
                                {/* Polaroid card */}
                                <div className="polaroid-card">
                                    <div className="pin"></div>
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
                        ))}
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="main-footer">
                <p>EXCEL TECHFEST 2025 // MASCOT_BOOTH_V2.1</p>
            </footer>

            <style jsx global>{`
                :root {
                    --bg-dark: #050505;
                    --gold: #D4A84B;
                    --gold-bright: #FFD700;
                    --orange: #E8943A;
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

                /* Background Image */
                .bg-image {
                    position: fixed;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background: url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1920&q=80');
                    background-size: cover;
                    background-position: center;
                    background-attachment: fixed;
                    filter: grayscale(100%) brightness(0.25) contrast(1.1);
                    z-index: -2;
                }

                .bg-overlay {
                    position: fixed;
                    top: 0; left: 0;
                    width: 100%; height: 100%;
                    background: 
                        radial-gradient(ellipse at 30% 20%, rgba(212, 168, 75, 0.12) 0%, transparent 50%),
                        radial-gradient(ellipse at 70% 80%, rgba(232, 148, 58, 0.08) 0%, transparent 50%),
                        linear-gradient(180deg, rgba(5, 5, 5, 0.3) 0%, rgba(5, 5, 5, 0.6) 100%);
                    z-index: -1;
                }

                /* Header */
                .mascot-header {
                    text-align: center;
                    padding: 50px 20px 30px;
                }

                .mascot-title {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 3rem;
                    font-weight: 700;
                    color: var(--gold);
                    letter-spacing: 10px;
                    text-shadow: 
                        0 0 30px rgba(212, 168, 75, 0.5),
                        0 0 60px rgba(212, 168, 75, 0.3);
                    margin-bottom: 10px;
                }

                .mascot-subtitle {
                    font-size: 0.8rem;
                    color: var(--text-dim);
                    letter-spacing: 3px;
                }

                /* Controls Panel */
                .controls-panel {
                    max-width: 850px;
                    margin: 0 auto 40px;
                    padding: 20px;
                    background: rgba(10, 10, 10, 0.85);
                    border: 1px solid var(--border);
                    border-left: 3px solid var(--gold);
                    backdrop-filter: blur(10px);
                }

                .panel-section {
                    margin-bottom: 15px;
                }

                .panel-section:last-child {
                    margin-bottom: 0;
                }

                .panel-label {
                    color: var(--text-dim);
                    font-size: 0.7rem;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #222;
                    display: inline-block;
                    padding-right: 15px;
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
                    color: var(--text);
                    padding: 8px 16px;
                    font-family: 'Share Tech Mono', monospace;
                    font-size: 0.8rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-transform: uppercase;
                }

                .filter-btn:hover {
                    border-color: var(--gold);
                    color: var(--gold);
                    box-shadow: 0 0 12px rgba(212, 168, 75, 0.3);
                }

                .filter-btn.active {
                    background: var(--gold);
                    color: #000;
                    border-color: var(--gold);
                    box-shadow: 0 0 20px rgba(212, 168, 75, 0.5);
                    font-weight: bold;
                }

                .mode-btn {
                    background: #0a0a0a;
                    border: 1px solid #333;
                    color: #777;
                    padding: 8px 14px;
                    font-family: 'Orbitron', sans-serif;
                    font-size: 0.75rem;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }

                .mode-btn:hover {
                    color: white;
                    border-color: white;
                }

                .mode-btn.active {
                    background: var(--gold);
                    color: black;
                    border-color: var(--gold);
                    box-shadow: 0 0 20px rgba(212, 168, 75, 0.5);
                    font-weight: bold;
                }

                /* Timeline Gallery */
                .timeline-container {
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 20px 20px 80px;
                    position: relative;
                    min-height: 400px;
                }

                .timeline-track {
                    position: relative;
                    padding-top: 30px;
                }

                /* Main vertical timeline line */
                .main-timeline-line {
                    position: absolute;
                    left: 50%;
                    top: 0;
                    bottom: 0;
                    width: 3px;
                    background: linear-gradient(180deg, var(--gold) 0%, var(--orange) 50%, var(--gold) 100%);
                    transform: translateX(-50%);
                    box-shadow: 0 0 15px rgba(212, 168, 75, 0.4);
                    z-index: 1;
                }

                /* Photo Node */
                .photo-node {
                    position: relative;
                    margin-bottom: 80px;
                    display: flex;
                    align-items: center;
                    min-height: 300px;
                }

                .photo-node.left {
                    justify-content: flex-start;
                    padding-right: calc(50% + 20px);
                }

                .photo-node.right {
                    justify-content: flex-end;
                    padding-left: calc(50% + 20px);
                }

                /* Branch line SVG */
                .branch-line {
                    position: absolute;
                    left: 50%;
                    top: 50%;
                    transform: translate(-50%, -50%);
                    width: 200px;
                    height: 100px;
                    z-index: 2;
                    pointer-events: none;
                }

                .photo-node.left .branch-line {
                    left: calc(50% - 100px);
                }

                .photo-node.right .branch-line {
                    left: calc(50% + 100px);
                }

                .branch-svg {
                    width: 100%;
                    height: 100%;
                    overflow: visible;
                }

                .branch-path {
                    fill: none;
                    stroke: #333;
                    stroke-width: 3;
                    stroke-dasharray: 400;
                    stroke-dashoffset: 400;
                    transition: stroke-dashoffset 1s ease-out, stroke 0.5s ease;
                }

                .photo-node.visible .branch-path {
                    stroke-dashoffset: 0;
                    stroke: var(--gold);
                    filter: drop-shadow(0 0 8px rgba(212, 168, 75, 0.6));
                }

                /* Timeline Dot */
                .timeline-dot {
                    position: absolute;
                    left: 50%;
                    top: 50%;
                    width: 16px;
                    height: 16px;
                    background: var(--bg-dark);
                    border: 3px solid #444;
                    border-radius: 50%;
                    transform: translate(-50%, -50%) scale(0);
                    z-index: 5;
                    transition: transform 0.4s ease 0.3s, border-color 0.3s ease, background 0.3s ease, box-shadow 0.3s ease;
                }

                .photo-node.visible .timeline-dot {
                    transform: translate(-50%, -50%) scale(1);
                    border-color: var(--gold);
                    background: var(--gold);
                    box-shadow: 0 0 20px rgba(212, 168, 75, 0.7);
                }

                /* Polaroid Card */
                .polaroid-card {
                    background: #f0ede5;
                    padding: 10px 10px 12px 10px;
                    box-shadow: 
                        0 10px 40px rgba(0, 0, 0, 0.7),
                        0 0 0 1px rgba(255, 255, 255, 0.05);
                    position: relative;
                    max-width: 280px;
                    transform: rotate(-3deg);
                    opacity: 0;
                    transition: transform 0.5s ease, box-shadow 0.4s ease, opacity 0.6s ease;
                    z-index: 3;
                }

                .photo-node.right .polaroid-card {
                    transform: rotate(3deg);
                }

                .photo-node.visible .polaroid-card {
                    opacity: 1;
                }

                .photo-node.new-photo .polaroid-card {
                    animation: popIn 0.7s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                }

                .polaroid-card:hover {
                    transform: rotate(0deg) scale(1.08);
                    box-shadow: 
                        0 20px 60px rgba(0, 0, 0, 0.8),
                        0 0 40px rgba(212, 168, 75, 0.3);
                    z-index: 20;
                }

                .pin {
                    position: absolute;
                    top: -10px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 20px;
                    height: 20px;
                    background: radial-gradient(circle at 30% 30%, #ffd700, #b8860b);
                    border-radius: 50%;
                    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.5);
                    z-index: 10;
                }

                .pin::after {
                    content: '';
                    position: absolute;
                    top: 4px;
                    left: 4px;
                    width: 5px;
                    height: 5px;
                    background: rgba(255, 255, 255, 0.8);
                    border-radius: 50%;
                }

                .photo-frame {
                    background: #000;
                    aspect-ratio: 1;
                    overflow: hidden;
                    margin-bottom: 10px;
                }

                .photo-frame img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                    filter: grayscale(100%) contrast(1.1);
                    transition: filter 0.5s ease;
                }

                .polaroid-card:hover .photo-frame img {
                    filter: grayscale(0%) contrast(1.05);
                }

                .photo-info {
                    font-family: 'Share Tech Mono', monospace;
                    color: #333;
                    font-size: 0.7rem;
                    margin-bottom: 6px;
                }

                .rec-date, .location {
                    margin: 2px 0;
                }

                .photo-footer {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 0.65rem;
                    color: #555;
                    margin-bottom: 8px;
                }

                .photo-id {
                    font-family: 'Share Tech Mono', monospace;
                }

                .excel-badge {
                    font-family: 'Share Tech Mono', monospace;
                    letter-spacing: 1px;
                }

                .download-btn {
                    width: 100%;
                    background: #222;
                    color: #ccc;
                    border: none;
                    padding: 8px;
                    font-family: 'Share Tech Mono', monospace;
                    font-size: 0.7rem;
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
                    padding: 80px;
                    color: var(--text-dim);
                }

                .spinner {
                    width: 45px;
                    height: 45px;
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
                    font-size: 0.65rem;
                    border-top: 1px solid var(--border);
                }

                /* Animations */
                @keyframes popIn {
                    0% {
                        opacity: 0;
                        transform: scale(0.3) rotate(-10deg);
                    }
                    60% {
                        transform: scale(1.1) rotate(2deg);
                    }
                    100% {
                        opacity: 1;
                        transform: scale(1) rotate(-3deg);
                    }
                }

                @keyframes spin {
                    to { transform: rotate(360deg); }
                }

                /* Responsive */
                @media (max-width: 768px) {
                    .mascot-title {
                        font-size: 2rem;
                        letter-spacing: 5px;
                    }

                    .photo-node.left,
                    .photo-node.right {
                        padding-left: 55px;
                        padding-right: 15px;
                        justify-content: flex-start;
                    }

                    .main-timeline-line {
                        left: 25px;
                    }

                    .timeline-dot {
                        left: 25px;
                    }

                    .branch-line {
                        display: none;
                    }

                    .polaroid-card,
                    .photo-node.right .polaroid-card {
                        transform: rotate(-2deg);
                        max-width: 240px;
                    }

                    .polaroid-card:hover {
                        transform: rotate(0deg) scale(1.05);
                    }

                    .controls-panel {
                        margin: 0 10px 30px;
                        padding: 15px;
                    }

                    .filter-btn, .mode-btn {
                        padding: 6px 12px;
                        font-size: 0.7rem;
                    }
                }
            `}</style>
        </div>
    );
}
