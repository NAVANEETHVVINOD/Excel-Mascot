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
    const timelineRef = useRef(null);
    const photoRefs = useRef({});

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
            { threshold: 0.2, rootMargin: '0px 0px -50px 0px' }
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

    return (
        <div className="page-container">
            <Head>
                <title>MASCOT - Excel Techfest 2025</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet" />
            </Head>

            {/* Background */}
            <div className="bg-overlay"></div>

            {/* MASCOT Heading */}
            <header className="mascot-header">
                <h1 className="mascot-title">MASCOT</h1>
                <p className="mascot-subtitle">EXCEL TECHFEST 2025 // PHOTO_BOOTH_V2.1</p>
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
            <main className="timeline-container" ref={timelineRef}>
                {loading ? (
                    <div className="loading-spinner">
                        <div className="spinner"></div>
                        <p>Loading memories...</p>
                    </div>
                ) : (
                    <>
                        <div className="timeline-track">
                            {photos.map((photo, index) => (
                                <div 
                                    key={photo.id} 
                                    className={`photo-node ${visiblePhotos.has(photo.id.toString()) ? 'visible' : ''} ${photo.isNew ? 'new-photo' : ''} ${index % 2 === 0 ? 'left' : 'right'}`}
                                    ref={el => photoRefs.current[photo.id] = el}
                                    data-id={photo.id}
                                >
                                    {/* Animated line segment */}
                                    <div className="line-segment">
                                        <div className="line-fill"></div>
                                    </div>
                                    
                                    {/* Connection curve to photo */}
                                    <svg className="curve-connector" viewBox="0 0 100 50" preserveAspectRatio="none">
                                        <path className="curve-path" d={index % 2 === 0 ? "M50,0 Q50,25 0,25" : "M50,0 Q50,25 100,25"} />
                                    </svg>
                                    
                                    {/* Timeline dot */}
                                    <div className="timeline-dot"></div>
                                    
                                    {/* Polaroid card */}
                                    <div className="polaroid-card">
                                        <div className="pin"></div>
                                        <div className="photo-frame">
                                            <img src={photo.image_url} alt="Memory" loading="lazy" />
                                        </div>
                                        <div className="photo-info">
                                            <p className="rec-date">REC_DATE: {formatDate(photo.created_at)}</p>
                                            <p className="location">LOC: REC</p>
                                        </div>
                                        <div className="photo-footer">
                                            <span className="photo-id">EXCEL_LOG_{String(index + 1).padStart(2, '0')}</span>
                                            <span className="excel-badge">[EXCELETED]</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </main>

            {/* Footer */}
            <footer className="main-footer">
                <p>EXCEL TECHFEST 2025 // MASCOT_BOOTH_V2.1</p>
            </footer>

            <style jsx global>{`
                :root {
                    --bg-dark: #050505;
                    --bg-card: #1a1a1a;
                    --gold: #FFD700;
                    --orange: #FF8C00;
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
                        radial-gradient(ellipse at 20% 30%, rgba(255, 140, 0, 0.08) 0%, transparent 50%),
                        radial-gradient(ellipse at 80% 70%, rgba(255, 215, 0, 0.05) 0%, transparent 50%),
                        url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
                    opacity: 0.4;
                    z-index: -1;
                }

                /* MASCOT Header */
                .mascot-header {
                    text-align: center;
                    padding: 60px 20px 40px;
                }

                .mascot-title {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 4rem;
                    font-weight: 900;
                    color: var(--gold);
                    letter-spacing: 15px;
                    text-shadow: 
                        0 0 20px rgba(255, 215, 0, 0.5),
                        0 0 40px rgba(255, 215, 0, 0.3),
                        0 0 60px rgba(255, 140, 0, 0.2);
                    margin-bottom: 15px;
                }

                .mascot-subtitle {
                    font-size: 0.85rem;
                    color: var(--text-dim);
                    letter-spacing: 3px;
                }

                /* Controls Panel */
                .controls-panel {
                    max-width: 900px;
                    margin: 0 auto 50px;
                    padding: 25px;
                    background: rgba(15, 15, 15, 0.9);
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
                    margin-bottom: 12px;
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
                    padding: 10px 22px;
                    font-family: 'Share Tech Mono', monospace;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-transform: uppercase;
                }

                .filter-btn:hover {
                    border-color: var(--gold);
                    color: var(--gold);
                    box-shadow: 0 0 15px rgba(255, 215, 0, 0.2);
                }

                .filter-btn.active {
                    background: var(--gold);
                    color: #000;
                    border-color: var(--gold);
                    box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
                    font-weight: bold;
                }

                .mode-btn {
                    background: #111;
                    border: 1px solid #333;
                    color: #888;
                    padding: 10px 18px;
                    font-family: 'Orbitron', sans-serif;
                    font-size: 0.85rem;
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
                    box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
                    font-weight: bold;
                }

                /* Timeline Gallery */
                .timeline-container {
                    max-width: 1100px;
                    margin: 0 auto;
                    padding: 40px 20px 100px;
                    position: relative;
                    min-height: 500px;
                }

                .timeline-track {
                    position: relative;
                    padding-top: 20px;
                }

                /* Photo Node */
                .photo-node {
                    position: relative;
                    margin-bottom: 100px;
                    display: flex;
                    align-items: flex-start;
                    opacity: 0;
                    transform: translateY(50px);
                    transition: opacity 0.8s ease, transform 0.8s ease;
                }

                .photo-node.visible {
                    opacity: 1;
                    transform: translateY(0);
                }

                .photo-node.new-photo {
                    animation: popIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                }

                .photo-node.left {
                    justify-content: flex-start;
                    padding-left: calc(50% + 30px);
                }

                .photo-node.right {
                    justify-content: flex-end;
                    padding-right: calc(50% + 30px);
                }

                /* Animated Line Segment */
                .line-segment {
                    position: absolute;
                    left: 50%;
                    top: -100px;
                    width: 4px;
                    height: 200px;
                    transform: translateX(-50%);
                    background: rgba(50, 50, 50, 0.5);
                    overflow: hidden;
                }

                .photo-node:first-child .line-segment {
                    top: 0;
                    height: 100px;
                }

                .line-fill {
                    width: 100%;
                    height: 0%;
                    background: linear-gradient(180deg, var(--gold) 0%, var(--orange) 100%);
                    transition: height 1s ease-out 0.3s;
                    box-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
                }

                .photo-node.visible .line-fill {
                    height: 100%;
                }

                /* Curve Connector */
                .curve-connector {
                    position: absolute;
                    top: 50px;
                    width: 120px;
                    height: 60px;
                    overflow: visible;
                }

                .photo-node.left .curve-connector {
                    left: calc(50% - 60px);
                }

                .photo-node.right .curve-connector {
                    right: calc(50% - 60px);
                    transform: scaleX(-1);
                }

                .curve-path {
                    fill: none;
                    stroke: rgba(50, 50, 50, 0.5);
                    stroke-width: 3;
                    stroke-dasharray: 150;
                    stroke-dashoffset: 150;
                    transition: stroke-dashoffset 0.8s ease-out 0.5s, stroke 0.5s ease;
                }

                .photo-node.visible .curve-path {
                    stroke-dashoffset: 0;
                    stroke: var(--gold);
                    filter: drop-shadow(0 0 5px rgba(255, 215, 0, 0.5));
                }

                /* Timeline Dot */
                .timeline-dot {
                    position: absolute;
                    left: 50%;
                    top: 50px;
                    width: 18px;
                    height: 18px;
                    background: var(--bg-dark);
                    border: 3px solid #333;
                    border-radius: 50%;
                    transform: translate(-50%, -50%) scale(0);
                    z-index: 5;
                    transition: transform 0.4s ease 0.6s, border-color 0.3s ease, box-shadow 0.3s ease;
                }

                .photo-node.visible .timeline-dot {
                    transform: translate(-50%, -50%) scale(1);
                    border-color: var(--gold);
                    background: var(--gold);
                    box-shadow: 0 0 15px rgba(255, 215, 0, 0.6);
                }

                /* Polaroid Card */
                .polaroid-card {
                    background: #f5f5f0;
                    padding: 12px 12px 15px 12px;
                    box-shadow: 
                        0 8px 30px rgba(0, 0, 0, 0.6),
                        0 0 0 1px rgba(255, 255, 255, 0.05);
                    position: relative;
                    max-width: 300px;
                    transform: rotate(-3deg);
                    transition: transform 0.4s ease, box-shadow 0.4s ease;
                }

                .photo-node.right .polaroid-card {
                    transform: rotate(3deg);
                }

                .polaroid-card:hover {
                    transform: rotate(0deg) scale(1.05);
                    box-shadow: 
                        0 15px 50px rgba(0, 0, 0, 0.7),
                        0 0 30px rgba(255, 215, 0, 0.3);
                    z-index: 10;
                }

                .pin {
                    position: absolute;
                    top: -10px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 22px;
                    height: 22px;
                    background: radial-gradient(circle at 30% 30%, #ffd700, #b8860b);
                    border-radius: 50%;
                    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
                    z-index: 10;
                }

                .pin::after {
                    content: '';
                    position: absolute;
                    top: 5px;
                    left: 5px;
                    width: 6px;
                    height: 6px;
                    background: rgba(255, 255, 255, 0.7);
                    border-radius: 50%;
                }

                .photo-frame {
                    background: #000;
                    aspect-ratio: 1;
                    overflow: hidden;
                    margin-bottom: 12px;
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
                    font-size: 0.75rem;
                    margin-bottom: 8px;
                }

                .rec-date, .location {
                    margin: 2px 0;
                }

                .photo-footer {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 0.7rem;
                    color: #666;
                }

                .photo-id {
                    font-family: 'Share Tech Mono', monospace;
                }

                .excel-badge {
                    font-family: 'Share Tech Mono', monospace;
                    letter-spacing: 1px;
                }

                /* Loading */
                .loading-spinner {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 100px;
                    color: var(--text-dim);
                }

                .spinner {
                    width: 50px;
                    height: 50px;
                    border: 3px solid var(--border);
                    border-top-color: var(--gold);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 20px;
                }

                /* Footer */
                .main-footer {
                    text-align: center;
                    padding: 40px;
                    color: var(--text-dim);
                    font-size: 0.7rem;
                    border-top: 1px solid var(--border);
                }

                /* Animations */
                @keyframes popIn {
                    0% {
                        opacity: 0;
                        transform: scale(0.5) translateY(50px);
                    }
                    70% {
                        transform: scale(1.1) translateY(0);
                    }
                    100% {
                        opacity: 1;
                        transform: scale(1) translateY(0);
                    }
                }

                @keyframes spin {
                    to { transform: rotate(360deg); }
                }

                /* Responsive */
                @media (max-width: 768px) {
                    .mascot-title {
                        font-size: 2.5rem;
                        letter-spacing: 8px;
                    }

                    .photo-node.left,
                    .photo-node.right {
                        padding-left: 60px;
                        padding-right: 20px;
                        justify-content: flex-start;
                    }

                    .line-segment {
                        left: 30px;
                    }

                    .timeline-dot {
                        left: 30px;
                    }

                    .curve-connector {
                        display: none;
                    }

                    .polaroid-card,
                    .photo-node.right .polaroid-card {
                        transform: rotate(-2deg);
                        max-width: 260px;
                    }

                    .controls-panel {
                        margin: 0 15px 40px;
                    }
                }
            `}</style>
        </div>
    );
}
