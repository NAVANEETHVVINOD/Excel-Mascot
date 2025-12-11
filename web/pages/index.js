import { supabase } from "../supabaseClient";
import { useEffect, useState } from "react";
import Head from "next/head";

export default function Gallery() {
    const [photos, setPhotos] = useState([]);
    const [viewMode, setViewMode] = useState("GALLERY"); // "GALLERY" or "LIVE"

    async function loadPhotos() {
        let { data, error } = await supabase
            .from("photos")
            .select("*")
            .order("created_at", { ascending: false });

        if (error) console.error("Error loading photos:", error);
        else setPhotos(data || []);
    }

    useEffect(() => {
        loadPhotos();

        // Realtime Subscription
        const channel = supabase
            .channel("photos-changes")
            .on(
                "postgres_changes",
                { event: "INSERT", schema: "public", table: "photos" },
                (payload) => {
                    console.log("New Photo!", payload);
                    // Prepend new photo
                    setPhotos((prev) => [payload.new, ...prev]);
                }
            )
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    return (
        <div className="container">
            <Head>
                <title>Mascot Cloud Gallery</title>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
            </Head>

            <header>
                <h1>☁️ Mascot Cloud Gallery</h1>
                <div className="controls">
                    <button
                        className={viewMode === "GALLERY" ? "active" : ""}
                        onClick={() => setViewMode("GALLERY")}
                    >
                        Gallery
                    </button>
                    <button
                        className={viewMode === "LIVE" ? "active" : ""}
                        onClick={() => setViewMode("LIVE")}
                    >
                        Live View
                    </button>
                </div>
            </header>

            {viewMode === "LIVE" && photos.length > 0 && (
                <div className="live-view">
                    <h2>🔴 Live Feed</h2>
                    <img src={photos[0].image_url} className="featured-photo" alt="Latest" />
                    <p className="timestamp">{new Date(photos[0].created_at).toLocaleTimeString()}</p>
                </div>
            )}

            {viewMode === "GALLERY" && (
                <div className="grid">
                    {photos.map((p) => (
                        <div key={p.id} className="card">
                            <img src={p.image_url} loading="lazy" alt="Mascot Photo" />
                        </div>
                    ))}
                </div>
            )}

            <style jsx global>{`
        body {
          background: #111;
          color: white;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          margin: 0;
          padding: 20px;
        }
        .container {
          max-width: 1200px;
          margin: 0 auto;
          text-align: center;
        }
        header { margin-bottom: 40px; }
        h1 { font-size: 2.5rem; margin-bottom: 20px; color: #00e5ff; }
        
        .controls button {
          background: #333;
          border: 1px solid #555;
          color: white;
          padding: 10px 20px;
          margin: 0 10px;
          border-radius: 20px;
          cursor: pointer;
          font-size: 1rem;
        }
        .controls button.active {
          background: #00e5ff;
          color: black;
          border-color: #00e5ff;
        }

        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 20px;
        }
        .card {
          background: #222;
          padding: 10px;
          border-radius: 10px;
          box-shadow: 0 4px 15px rgba(0,0,0,0.5);
          transition: transform 0.2s;
        }
        .card:hover { transform: scale(1.02); }
        .card img {
          width: 100%;
          height: auto;
          border-radius: 5px;
          display: block;
        }

        .live-view {
          margin-top: 20px;
        }
        .featured-photo {
          max-width: 90%;
          max-height: 70vh;
          border: 5px solid white;
          box-shadow: 0 0 30px rgba(0, 229, 255, 0.3);
          border-radius: 10px;
        }
        .timestamp { color: #888; margin-top: 10px; }
      `}</style>
        </div>
    );
}
