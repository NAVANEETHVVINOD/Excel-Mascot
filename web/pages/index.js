import { supabase } from "../supabaseClient";
import { useEffect, useState, useRef } from "react";
import Head from "next/head";

const LOCAL_API_BASE = "http://localhost:5000";
const PHOTOS_PER_PAGE = 25;

export default function Gallery() {
    const [allPhotos, setAllPhotos] = useState([]);  // All photos from DB
    const [displayCount, setDisplayCount] = useState(PHOTOS_PER_PAGE);  // How many to show
    const [activeMode, setActiveMode] = useState('SINGLE');
    const [activeFilter, setActiveFilter] = useState('NORMAL');
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [visiblePhotos, setVisiblePhotos] = useState({});
    const [isLocal, setIsLocal] = useState(false);
    const photoRefs = useRef({});
    
    // Get only the photos to display (paginated)
    const photos = allPhotos.slice(0, displayCount);
    const hasMore = displayCount < allPhotos.length;
    const totalPhotos = allPhotos.length;

    useEffect(() => {
        // DETECT ENVIRONMENT
        const clsHelper = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
        setIsLocal(clsHelper);

        // Register Service Worker for PWA support
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').then(
                    registration => console.log('SW registered: ', registration.scope),
                    err => console.log('SW registration failed: ', err)
                );
            });
        }

        loadPhotos(false, clsHelper); // Initial Load

        if (clsHelper) {
            syncStatus();
            // POLL Local API for changes (Simulating Realtime)
            const intervalId = setInterval(() => {
                loadPhotos(true, true); // Silent reload
                syncStatus();     // Sync mode/filter
            }, 3000);
            return () => clearInterval(intervalId);
        } else {
            // SUPABASE REALTIME SUBSCRIPTION
            const subscription = supabase
                .channel('public:photos')
                .on('postgres_changes', { event: '*', schema: 'public', table: 'photos' }, (payload) => {
                    console.log('Realtime update:', payload);
                    loadPhotos(true, false);
                })
                .subscribe();

            return () => supabase.removeChannel(subscription);
        }
    }, []);

    // Intersection Observer for fade-in animation
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    const id = entry.target.dataset.id;
                    if (entry.isIntersecting) {
                        setVisiblePhotos(prev => ({ ...prev, [id]: true }));
                    }
                });
            },
            { threshold: 0.1, rootMargin: '50px' }
        );

        Object.values(photoRefs.current).forEach(ref => {
            if (ref) observer.observe(ref);
        });

        return () => observer.disconnect();
    }, [photos]);

    async function loadPhotos(silent = false, forceLocal = false) {
        if (!silent) setLoading(true);
        try {
            let formatted = [];

            if (forceLocal) {
                // --- LOCAL SAVED FILES ---
                try {
                    const res = await fetch(`${LOCAL_API_BASE}/api/photos?t=${Date.now()}`);
                    if (!res.ok) throw new Error('Local server not available');
                    const data = await res.json();
                    formatted = data.map(p => ({
                        id: p.id,
                        image_url: p.url,
                        created_at: new Date(p.created_at * 1000).toISOString(),
                        isNew: false
                    }));
                } catch (localErr) {
                    // Local server not running, fall back to Supabase
                    console.log('Local server unavailable, using Supabase...');
                    const { data, error } = await supabase
                        .from('photos')
                        .select('*')
                        .order('created_at', { ascending: false });

                    if (error) throw error;

                    formatted = data.map(p => ({
                        id: p.id,
                        image_url: p.image_url,
                        created_at: p.created_at,
                        isNew: false
                    }));
                }
            } else {
                // --- SUPABASE CLOUD ---
                const { data, error } = await supabase
                    .from('photos')
                    .select('*')
                    .order('created_at', { ascending: false });

                if (error) throw error;

                formatted = data.map(p => ({
                    id: p.id,
                    image_url: p.image_url,
                    created_at: p.created_at,
                    isNew: false
                }));
            }

            setAllPhotos(prev => {
                const existingIds = new Set(prev.map(p => p.id));
                const withNewFlag = formatted.map(p => ({
                    ...p,
                    isNew: !existingIds.has(p.id)
                }));
                return withNewFlag;
            });

        } catch (err) {
            console.error("Failed to load photos:", err);
        }
        if (!silent) setLoading(false);
    }

    // Load more photos
    const loadMore = () => {
        setLoadingMore(true);
        setTimeout(() => {
            setDisplayCount(prev => Math.min(prev + PHOTOS_PER_PAGE, allPhotos.length));
            setLoadingMore(false);
        }, 300);
    };

    // REMOVE BROKEN IMAGES (Black Cards) and clean up orphaned DB records
    const handleImageError = async (id) => {
        console.warn(`Image load failed for ID: ${id}. Removing from display and database.`);
        
        // Remove from local state immediately
        setAllPhotos(prev => prev.filter(photo => photo.id !== id));
        
        // Also delete the orphaned record from database (async, don't wait)
        try {
            await supabase
                .from('photos')
                .delete()
                .eq('id', id);
            console.log(`🗑️ Cleaned up orphaned DB record: ${id}`);
        } catch (err) {
            console.error(`Failed to clean up orphaned record ${id}:`, err);
        }
    };

    async function syncStatus() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout
            
            const res = await fetch(`${LOCAL_API_BASE}/get_filter`, { signal: controller.signal });
            clearTimeout(timeoutId);
            
            if (!res.ok) return;
            const data = await res.json();
            if (data.filter) setActiveFilter(data.filter);
            if (data.mode) setActiveMode(data.mode);
        } catch (e) { 
            // Silently ignore - local server not running
        }
    }

    const setMode = async (mode) => {
        setActiveMode(mode);
        try {
            // Always send to local Flask server if running locally
            if (isLocal) await fetch(`${LOCAL_API_BASE}/set_mode/${mode}`);
            
            // ALWAYS send Supabase broadcast (for remote control from cloud)
            await supabase.channel('booth_control').send({
                type: 'broadcast',
                event: 'command',
                payload: { type: 'SET_MODE', mode: mode }
            });
            console.log(`📡 Broadcast: SET_MODE ${mode}`);
        } catch (e) { console.error(e); }
    };

    const setFilter = async (filter) => {
        const newFilter = (activeFilter === filter) ? 'NORMAL' : filter;
        setActiveFilter(newFilter);
        try {
            // Always send to local Flask server if running locally
            if (isLocal) await fetch(`${LOCAL_API_BASE}/set_filter/${newFilter}`);
            
            // ALWAYS send Supabase broadcast (for remote control from cloud)
            await supabase.channel('booth_control').send({
                type: 'broadcast',
                event: 'command',
                payload: { type: 'SET_FILTER', filter: newFilter }
            });
            console.log(`📡 Broadcast: SET_FILTER ${newFilter}`);
        } catch (e) { console.error(e); }
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return `${String(date.getDate()).padStart(2, '0')}.${String(date.getMonth() + 1).padStart(2, '0')}.${date.getFullYear()}`;
    };

    const downloadPhoto = async (url, filename) => {
        try {
            const response = await fetch(url);
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = filename || 'excel_mascot_photo.jpg';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(blobUrl);
        } catch (err) {
            window.open(url, '_blank');
        }
    };

    const deletePhoto = async (photoId, imageUrl) => {
        if (!confirm('Are you sure you want to delete this photo?')) return;
        
        try {
            let deleteSuccess = false;
            
            // Extract filename from URL
            // Supabase URL format: https://xxx.supabase.co/storage/v1/object/public/photos/filename.jpg
            // Local URL format: http://localhost:5000/photos/filename.jpg
            const urlParts = imageUrl.split('/');
            const filename = urlParts[urlParts.length - 1];
            
            // Try local server first if running locally
            if (isLocal) {
                try {
                    const res = await fetch(`${LOCAL_API_BASE}/delete/${filename}`, { method: 'DELETE' });
                    if (res.ok) {
                        deleteSuccess = true;
                    }
                } catch (localErr) {
                    // Local server not available, will try Supabase
                    console.log('Local server unavailable, using Supabase for delete...');
                }
            }
            
            // If local delete didn't work or not local, use Supabase
            if (!deleteSuccess) {
                // 1. Delete from Storage bucket
                const { error: storageError } = await supabase.storage
                    .from('photos')
                    .remove([filename]);
                
                if (storageError) {
                    console.error('Storage delete error:', storageError);
                    // Continue anyway - file might already be deleted or have different name
                }
                
                // 2. Delete from Database by ID (most reliable)
                const { error: dbError } = await supabase
                    .from('photos')
                    .delete()
                    .eq('id', photoId);
                
                if (dbError) {
                    console.error('Database delete error:', dbError);
                    throw dbError;
                }
            }
            
            // Remove from local state
            setAllPhotos(prev => prev.filter(p => p.id !== photoId));
            console.log('🗑️ Photo deleted successfully');
            
        } catch (err) {
            console.error('Failed to delete photo:', err);
            alert('Failed to delete photo. Please try again.');
        }
    };

    return (
        <div className="page-container">
            <Head>
                <title>EXCEL MASCOT - Techfest 2025</title>
                <meta name="description" content="Excel Techfest 2025 Mascot Photo Booth Gallery" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes" />
                <meta name="theme-color" content="#FFB800" />
                <meta name="mobile-web-app-capable" content="yes" />
                <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
                <link rel="manifest" href="/manifest.json" />
                <link rel="icon" type="image/webp" href="/logo.webp" />
                <link rel="apple-touch-icon" href="/logo.webp" />
                {/* Retro Pixel Fonts */}
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
                <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet" />
            </Head>

            {/* ===== ANIMATED BACKGROUND ===== */}
            <div className="bg-container">
                <div className="orb orb-1"></div>
                <div className="orb orb-2"></div>
                <div className="orb orb-3"></div>
                <div className="grain-overlay"></div>
                <div className="grid-overlay"></div>
            </div>

            {/* ===== EXCEL LOGO - TOP RIGHT ===== */}
            <img src="/logo.webp" alt="Excel Logo" className="corner-logo" />

            {/* ===== HEADER ===== */}
            <header className="main-header">
                <h1 className="main-title">EXCEL 2025</h1>
                <p className="main-subtitle">Mascot Photo Booth // Gallery</p>
                <div className="header-divider">
                    <span className="divider-line left"></span>
                    <svg className="sparkle" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" />
                    </svg>
                    <span className="divider-line right"></span>
                </div>
            </header>

            {/* ===== CONTROL PANEL ===== */}
            <section className="controls-section">
                <div className="controls-panel">
                    <div className="panel-row">
                        <div className="panel-header">
                            <svg className="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                            </svg>
                            <span className="panel-label">/// FILTERS</span>
                        </div>
                        <div className="btn-group">
                            {['NORMAL', 'NEON', 'NOIR', 'RETRO', 'DREAMY', 'GLITCH', 'B&W'].map(f => (
                                <button
                                    key={f}
                                    className={`ctrl-btn ${activeFilter === f ? 'active' : ''}`}
                                    onClick={() => setFilter(f)}
                                >
                                    {f}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="panel-row">
                        <div className="panel-header">
                            <svg className="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                                <circle cx="12" cy="13" r="4" />
                            </svg>
                            <span className="panel-label">/// MODE</span>
                        </div>
                        <div className="btn-group mode-group">
                            {['SINGLE', 'BURST', 'GIF'].map(m => (
                                <button
                                    key={m}
                                    className={`ctrl-btn mode-btn ${activeMode === m ? 'active' : ''}`}
                                    onClick={() => setMode(m)}
                                >
                                    {m}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* ===== PHOTO GALLERY ===== */}
            <main className="gallery-section">
                <h2 className="section-title">CAPTURED MOMENTS</h2>
                <p className="photo-count">Showing {photos.length} of {totalPhotos} photos</p>

                {loading ? (
                    <div className="loading-state">
                        <div className="loader"></div>
                        <p>Loading memories...</p>
                    </div>
                ) : photos.length === 0 ? (
                    <div className="empty-state">
                        <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                            <circle cx="12" cy="13" r="4" />
                        </svg>
                        <p>No photos yet</p>
                        <span>Show a thumbs up to capture!</span>
                    </div>
                ) : (
                    <>
                        <div className="photo-grid">
                            {photos.map((photo, index) => {
                                const isVisible = visiblePhotos[photo.id];

                                return (
                                    <div
                                        key={photo.id}
                                        className={`photo-card ${isVisible ? 'visible' : ''} ${photo.isNew ? 'new' : ''}`}
                                        ref={el => photoRefs.current[photo.id] = el}
                                        data-id={photo.id}
                                        style={{
                                            animationDelay: `${(index % 6) * 0.1}s`,
                                            transform: `rotate(${(index % 2 === 0 ? -2 : 2) + (index % 3)}deg)`
                                        }}
                                    >
                                        {/* Tape */}
                                        <div className="tape"></div>

                                        {/* Photo Frame */}
                                        <div className="photo-frame">
                                            <img
                                                src={photo.image_url}
                                                alt={`Photo ${index + 1}`}
                                                loading="lazy"
                                                onError={() => handleImageError(photo.id)}
                                            />
                                            <div className="photo-overlay">
                                                <button
                                                    className="action-btn download-btn"
                                                    onClick={() => downloadPhoto(photo.image_url, `excel_${photo.id}.jpg`)}
                                                    aria-label="Download"
                                                >
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                                        <polyline points="7 10 12 15 17 10" />
                                                        <line x1="12" y1="15" x2="12" y2="3" />
                                                    </svg>
                                                </button>
                                                <button
                                                    className="action-btn delete-btn"
                                                    onClick={() => deletePhoto(photo.id, photo.image_url)}
                                                    aria-label="Delete"
                                                >
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <polyline points="3 6 5 6 21 6" />
                                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                                                        <line x1="10" y1="11" x2="10" y2="17" />
                                                        <line x1="14" y1="11" x2="14" y2="17" />
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>

                                        {/* Polaroid Caption Area */}
                                        <div className="polaroid-caption">
                                            <span className="log-id">EXCEL_LOG_{String(index + 1).padStart(2, '0')}</span>
                                            <span className="photo-date">{formatDate(photo.created_at)}</span>
                                        </div>

                                        {/* EXCELETED Stamp */}
                                        <div className="stamp">EXCELETED</div>
                                    </div>
                                );
                            })}
                        </div>
                        
                        {/* Load More Button */}
                        {hasMore && (
                            <div className="load-more-container">
                                <button 
                                    className="load-more-btn"
                                    onClick={loadMore}
                                    disabled={loadingMore}
                                >
                                    {loadingMore ? (
                                        <>
                                            <span className="btn-loader"></span>
                                            Loading...
                                        </>
                                    ) : (
                                        <>
                                            LOAD MORE
                                            <span className="remaining-count">({totalPhotos - displayCount} remaining)</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        )}
                    </>
                )}
            </main>

            {/* ===== FOOTER ===== */}
            <footer className="main-footer">
                <div className="footer-border"></div>
                <p className="footer-title">EXCEL TECHFEST 2025</p>
                <p className="footer-sub">Model Engineering College, Thrikkakara</p>
            </footer>

            <style jsx global>{`
                /* ========== CSS VARIABLES ========== */
                :root {
                    --gold: #FFB800;
                    --orange: #FF6B00;
                    --amber: #FFAD33;
                    --black: #000000;
                    --charcoal: #0a0a0a;
                    --dark-gray: #1a1a1a;
                    --gray: #333333;
                    --muted: #666666;
                    --cream: #f5f5f0;
                }

                /* ========== BASE RESET ========== */
                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }

                html {
                    scroll-behavior: smooth;
                }

                body {
                    background: var(--black);
                    color: #fff;
                    font-family: 'VT323', 'Share Tech Mono', monospace;
                    font-size: 18px;
                    min-height: 100vh;
                    overflow-x: hidden;
                    -webkit-font-smoothing: none;
                    image-rendering: pixelated;
                }

                .page-container {
                    position: relative;
                    min-height: 100vh;
                }

                /* ========== ANIMATED BACKGROUND ========== */
                .bg-container {
                    position: fixed;
                    inset: 0;
                    z-index: 0;
                    pointer-events: none;
                    overflow: hidden;
                }

                .orb {
                    position: absolute;
                    border-radius: 50%;
                    mix-blend-mode: screen;
                    filter: blur(80px);
                    animation: orbPulse 8s ease-in-out infinite;
                }

                .orb-1 {
                    top: -10%;
                    left: 20%;
                    width: 500px;
                    height: 500px;
                    background: radial-gradient(circle, rgba(255, 107, 0, 0.4) 0%, transparent 70%);
                }

                .orb-2 {
                    top: 30%;
                    right: 10%;
                    width: 400px;
                    height: 400px;
                    background: radial-gradient(circle, rgba(255, 184, 0, 0.35) 0%, transparent 70%);
                    animation-delay: 2s;
                }

                .orb-3 {
                    bottom: -5%;
                    left: 40%;
                    width: 450px;
                    height: 450px;
                    background: radial-gradient(circle, rgba(255, 140, 0, 0.3) 0%, transparent 70%);
                    animation-delay: 4s;
                }

                @keyframes orbPulse {
                    0%, 100% { transform: scale(1) translate(0, 0); opacity: 0.6; }
                    25% { transform: scale(1.1) translate(20px, -10px); opacity: 0.8; }
                    50% { transform: scale(0.95) translate(-10px, 20px); opacity: 0.5; }
                    75% { transform: scale(1.05) translate(-20px, -15px); opacity: 0.7; }
                }

                .grain-overlay {
                    position: absolute;
                    inset: 0;
                    opacity: 0.4;
                    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
                    background-repeat: repeat;
                    background-size: 100px 100px;
                }

                .grid-overlay {
                    position: absolute;
                    inset: 0;
                    opacity: 0.06;
                    background-image: 
                        linear-gradient(rgba(255, 184, 0, 0.3) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(255, 184, 0, 0.3) 1px, transparent 1px);
                    background-size: 60px 60px;
                }

                /* ========== CORNER LOGO ========== */
                .corner-logo {
                    position: fixed;
                    top: 16px;
                    left: 16px;
                    width: 70px;
                    height: 70px;
                    object-fit: contain;
                    z-index: 100;
                    filter: drop-shadow(0 0 15px rgba(255, 184, 0, 0.6));
                    transition: transform 0.3s ease, filter 0.3s ease;
                }

                .corner-logo:hover {
                    transform: scale(1.1);
                    filter: drop-shadow(0 0 25px rgba(255, 184, 0, 0.8));
                }

                /* ========== HEADER ========== */
                .main-header {
                    position: relative;
                    z-index: 10;
                    text-align: center;
                    padding: 50px 20px 30px;
                }

                .main-title {
                    font-family: 'Press Start 2P', cursive;
                    font-size: clamp(1.2rem, 5vw, 2.2rem);
                    font-weight: 400;
                    letter-spacing: 2px;
                    background: linear-gradient(135deg, var(--gold) 0%, var(--orange) 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    text-shadow: 0 0 30px rgba(255, 184, 0, 0.4);
                    line-height: 1.4;
                }

                .main-subtitle {
                    font-family: 'VT323', monospace;
                    color: var(--gold);
                    font-size: 1.2rem;
                    letter-spacing: 4px;
                    text-transform: uppercase;
                    margin-top: 8px;
                }

                .header-divider {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 16px;
                    margin-top: 20px;
                }

                .divider-line {
                    width: 60px;
                    height: 1px;
                }

                .divider-line.left {
                    background: linear-gradient(to right, transparent, var(--gold));
                }

                .divider-line.right {
                    background: linear-gradient(to left, transparent, var(--gold));
                }

                .sparkle {
                    width: 14px;
                    height: 14px;
                    color: var(--gold);
                }

                /* ========== CONTROLS PANEL ========== */
                .controls-section {
                    position: relative;
                    z-index: 10;
                    padding: 0 16px;
                    margin-bottom: 40px;
                }

                .controls-panel {
                    max-width: 700px;
                    margin: 0 auto;
                    background: rgba(0, 0, 0, 0.5);
                    backdrop-filter: blur(16px);
                    border: 1px solid rgba(255, 140, 0, 0.2);
                    border-radius: 16px;
                    padding: 20px;
                }

                .panel-row {
                    margin-bottom: 16px;
                }

                .panel-row:last-child {
                    margin-bottom: 0;
                }

                .panel-header {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 10px;
                }

                .panel-icon {
                    width: 16px;
                    height: 16px;
                    color: var(--gold);
                }

                .panel-label {
                    font-size: 0.7rem;
                    color: var(--gold);
                    letter-spacing: 2px;
                }

                .btn-group {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                }

                .mode-group {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                }

                .ctrl-btn {
                    background: rgba(0, 0, 0, 0.6);
                    border: 2px solid rgba(255, 140, 0, 0.4);
                    color: var(--gold);
                    padding: 10px 14px;
                    font-family: 'VT323', monospace;
                    font-size: 1rem;
                    letter-spacing: 2px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .ctrl-btn:hover {
                    border-color: var(--orange);
                    background: rgba(255, 107, 0, 0.1);
                }

                .ctrl-btn.active {
                    background: linear-gradient(135deg, var(--orange), var(--gold));
                    border-color: var(--gold);
                    color: #000;
                    font-weight: 600;
                    box-shadow: 0 0 20px rgba(255, 140, 0, 0.4);
                }

                .mode-btn {
                    font-family: 'Press Start 2P', cursive;
                    font-size: 0.55rem;
                    text-align: center;
                    padding: 12px 10px;
                }

                /* ========== GALLERY SECTION ========== */
                .gallery-section {
                    position: relative;
                    z-index: 10;
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 0 16px 60px;
                }

                .section-title {
                    font-family: 'Press Start 2P', cursive;
                    font-size: clamp(0.8rem, 3vw, 1.2rem);
                    text-align: center;
                    background: linear-gradient(135deg, var(--gold) 0%, var(--orange) 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    margin-bottom: 8px;
                    line-height: 1.5;
                }

                .photo-count {
                    text-align: center;
                    color: var(--gold);
                    font-family: 'VT323', monospace;
                    font-size: 1.2rem;
                    margin-bottom: 40px;
                    letter-spacing: 2px;
                }

                /* ========== LOAD MORE BUTTON ========== */
                .load-more-container {
                    display: flex;
                    justify-content: center;
                    padding: 40px 20px;
                }

                .load-more-btn {
                    background: linear-gradient(135deg, var(--orange), var(--gold));
                    border: none;
                    color: #000;
                    font-family: 'Press Start 2P', cursive;
                    font-size: 0.7rem;
                    padding: 16px 32px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    box-shadow: 0 4px 20px rgba(255, 140, 0, 0.4);
                }

                .load-more-btn:hover:not(:disabled) {
                    transform: scale(1.05);
                    box-shadow: 0 8px 30px rgba(255, 140, 0, 0.6);
                }

                .load-more-btn:disabled {
                    opacity: 0.7;
                    cursor: not-allowed;
                }

                .remaining-count {
                    font-family: 'VT323', monospace;
                    font-size: 1rem;
                    opacity: 0.8;
                }

                .btn-loader {
                    width: 16px;
                    height: 16px;
                    border: 2px solid rgba(0, 0, 0, 0.2);
                    border-top-color: #000;
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                }

                /* ========== PHOTO GRID ========== */
                .photo-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 40px;
                    padding: 20px;
                }

                /* ========== POLAROID PHOTO CARD ========== */
                .photo-card {
                    position: relative;
                    background: linear-gradient(145deg, #f8f6f0, #e8e4dc);
                    padding: 14px 14px 50px 14px;
                    opacity: 0;
                    transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 
                        0 8px 25px rgba(0, 0, 0, 0.4),
                        0 3px 8px rgba(0, 0, 0, 0.2),
                        inset 0 1px 0 rgba(255, 255, 255, 0.5);
                }

                .photo-card.visible {
                    opacity: 1;
                }

                .photo-card:hover {
                    transform: scale(1.05) rotate(0deg) !important;
                    box-shadow: 
                        0 25px 60px rgba(0, 0, 0, 0.5),
                        0 10px 20px rgba(0, 0, 0, 0.3),
                        0 0 40px rgba(255, 140, 0, 0.15);
                    z-index: 10;
                }

                .photo-card.new {
                    animation: newCard 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
                }

                @keyframes newCard {
                    0% { opacity: 0; transform: scale(0.8) rotate(-10deg); }
                    100% { opacity: 1; transform: scale(1); }
                }

                /* Tape */
                .tape {
                    position: absolute;
                    top: -14px;
                    left: 50%;
                    transform: translateX(-50%) rotate(2deg);
                    width: 80px;
                    height: 28px;
                    background: linear-gradient(135deg, 
                        rgba(255, 210, 120, 0.75), 
                        rgba(255, 190, 100, 0.6));
                    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
                    z-index: 15;
                }

                .photo-frame {
                    position: relative;
                    aspect-ratio: 3/4;
                    overflow: hidden;
                    background: #111;
                }

                .photo-frame img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    filter: grayscale(100%);
                    transition: filter 0.5s ease, transform 0.5s ease;
                }

                .photo-card:hover .photo-frame img {
                    filter: grayscale(0%);
                    transform: scale(1.03);
                }

                .photo-overlay {
                    position: absolute;
                    inset: 0;
                    background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.3) 50%, transparent 100%);
                    opacity: 0;
                    transition: opacity 0.3s ease;
                    display: flex;
                    align-items: flex-end;
                    justify-content: center;
                    gap: 12px;
                    padding-bottom: 20px;
                }

                .photo-card:hover .photo-overlay {
                    opacity: 1;
                }

                .action-btn {
                    width: 44px;
                    height: 44px;
                    border: none;
                    border-radius: 50%;
                    color: #000;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transform: translateY(20px);
                    transition: all 0.3s ease;
                }

                .action-btn svg {
                    width: 20px;
                    height: 20px;
                }

                .photo-card:hover .action-btn {
                    transform: translateY(0);
                }

                .download-btn {
                    background: linear-gradient(135deg, var(--orange), var(--gold));
                    box-shadow: 0 4px 20px rgba(255, 140, 0, 0.5);
                }

                .download-btn:hover {
                    transform: scale(1.15) translateY(0) !important;
                    box-shadow: 0 8px 30px rgba(255, 140, 0, 0.7);
                }

                .delete-btn {
                    background: linear-gradient(135deg, #ff4444, #cc0000);
                    box-shadow: 0 4px 20px rgba(255, 0, 0, 0.4);
                }

                .delete-btn:hover {
                    transform: scale(1.15) translateY(0) !important;
                    box-shadow: 0 8px 30px rgba(255, 0, 0, 0.6);
                }

                /* Polaroid Caption */
                .polaroid-caption {
                    position: absolute;
                    bottom: 10px;
                    left: 14px;
                    right: 14px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .log-id {
                    font-size: 0.7rem;
                    color: #444;
                    letter-spacing: 1px;
                }

                .photo-date {
                    font-size: 0.65rem;
                    color: #777;
                }

                /* EXCELETED Stamp */
                .stamp {
                    position: absolute;
                    top: 30px;
                    right: -6px;
                    background: linear-gradient(135deg, var(--orange), #cc5500);
                    color: #fff;
                    font-family: 'Orbitron', sans-serif;
                    font-size: 0.55rem;
                    font-weight: 700;
                    padding: 5px 12px;
                    transform: rotate(12deg);
                    letter-spacing: 1.5px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
                }

                /* ========== LOADING & EMPTY STATES ========== */
                .loading-state, .empty-state {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 80px 20px;
                    text-align: center;
                }

                .loader {
                    width: 50px;
                    height: 50px;
                    border: 2px solid rgba(255, 140, 0, 0.2);
                    border-top-color: var(--gold);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 20px;
                }

                @keyframes spin {
                    to { transform: rotate(360deg); }
                }

                .loading-state p {
                    color: var(--muted);
                }

                .empty-icon {
                    width: 60px;
                    height: 60px;
                    color: #444;
                    margin-bottom: 16px;
                }

                .empty-state p {
                    color: var(--muted);
                    margin-bottom: 8px;
                }

                .empty-state span {
                    color: #555;
                    font-size: 0.8rem;
                }

                /* ========== FOOTER ========== */
                .main-footer {
                    position: relative;
                    z-index: 10;
                    text-align: center;
                    padding: 40px 20px;
                }

                .footer-border {
                    height: 1px;
                    max-width: 150px;
                    margin: 0 auto 20px;
                    background: linear-gradient(to right, transparent, rgba(255, 140, 0, 0.3), transparent);
                }

                .footer-title {
                    font-family: 'Orbitron', sans-serif;
                    font-size: 0.7rem;
                    color: var(--gold);
                    letter-spacing: 3px;
                    margin-bottom: 6px;
                }

                .footer-sub {
                    font-size: 0.65rem;
                    color: #555;
                }

                /* ========== MOBILE RESPONSIVE ========== */
                @media (max-width: 768px) {
                    .orb-1, .orb-2, .orb-3 {
                        width: 200px;
                        height: 200px;
                    }

                    .corner-logo {
                        width: 55px;
                        height: 55px;
                        top: 12px;
                        left: 12px;
                    }

                    .main-header {
                        padding: 35px 16px 20px;
                    }

                    .main-title {
                        font-size: 2rem;
                    }

                    .main-subtitle {
                        font-size: 0.65rem;
                        letter-spacing: 2px;
                    }

                    .controls-section {
                        margin-bottom: 30px;
                    }

                    .controls-panel {
                        padding: 14px;
                    }

                    .ctrl-btn {
                        padding: 8px 10px;
                        font-size: 0.55rem;
                    }

                    .section-title {
                        font-size: 1.3rem;
                        margin-bottom: 6px;
                    }

                    .photo-count {
                        margin-bottom: 25px;
                    }

                    /* 2-column grid on tablet/mobile */
                    .photo-grid {
                        grid-template-columns: repeat(2, 1fr);
                        gap: 20px;
                        padding: 10px;
                    }

                    .photo-card {
                        padding: 8px 8px 40px 8px;
                    }

                    .tape {
                        width: 60px;
                        height: 22px;
                        top: -10px;
                    }

                    .polaroid-caption {
                        bottom: 8px;
                        left: 8px;
                        right: 8px;
                    }

                    .log-id {
                        font-size: 0.55rem;
                    }

                    .photo-date {
                        font-size: 0.5rem;
                    }

                    .stamp {
                        font-size: 0.45rem;
                        padding: 3px 7px;
                        top: 20px;
                        right: -4px;
                    }

                    .download-btn, .delete-btn {
                        width: 36px;
                        height: 36px;
                    }

                    .download-btn svg, .delete-btn svg {
                        width: 16px;
                        height: 16px;
                    }

                    .load-more-btn {
                        font-size: 0.6rem;
                        padding: 14px 24px;
                    }

                    .remaining-count {
                        font-size: 0.9rem;
                    }

                    .footer-title {
                        font-size: 0.6rem;
                    }

                    .footer-sub {
                        font-size: 0.55rem;
                    }
                }

                @media (max-width: 480px) {
                    .corner-logo {
                        width: 45px;
                        height: 45px;
                        top: 10px;
                        left: 10px;
                    }

                    .main-title {
                        font-size: 1.8rem;
                    }

                    .btn-group {
                        gap: 5px;
                    }

                    .ctrl-btn {
                        padding: 7px 8px;
                        font-size: 0.5rem;
                        letter-spacing: 1px;
                    }

                    /* Keep 2 columns on small phones */
                    .photo-grid {
                        grid-template-columns: repeat(2, 1fr);
                        gap: 14px;
                        padding: 8px;
                    }

                    .photo-card {
                        padding: 6px 6px 35px 6px;
                    }

                    .tape {
                        width: 50px;
                        height: 18px;
                        top: -8px;
                    }

                    .polaroid-caption {
                        bottom: 6px;
                        left: 6px;
                        right: 6px;
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 2px;
                    }

                    .log-id {
                        font-size: 0.5rem;
                    }

                    .stamp {
                        font-size: 0.4rem;
                        padding: 2px 6px;
                        top: 16px;
                        right: -3px;
                    }

                    .download-btn, .delete-btn {
                        width: 32px;
                        height: 32px;
                    }

                    .download-btn svg, .delete-btn svg {
                        width: 14px;
                        height: 14px;
                    }
                }

                /* PWA Standalone */
                @media (display-mode: standalone) {
                    .main-header {
                        padding-top: 50px;
                    }
                }
            `}</style>
        </div>
    );
}
