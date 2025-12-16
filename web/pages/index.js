import { supabase } from "../supabaseClient";
import { useEffect, useState } from "react";
import Head from "next/head";

export default function Gallery() {
    const [photos, setPhotos] = useState([]);

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
        const channel = supabase
            .channel("photos-changes")
            .on(
                "postgres_changes",
                { event: "INSERT", schema: "public", table: "photos" },
                (payload) => {
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
                <title>Mascot Gallery</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&display=swap" rel="stylesheet" />
            </Head>

            <h1>MASCOT MEMORIES</h1>
            <div className="subtitle">Tech Fest 2k25</div>

            <div className="gallery">
                {photos.map((p, index) => (
                    <div key={p.id} className={`photo-card ${index % 2 === 0 ? 'rotate-left' : 'rotate-right'}`}>
                        <img src={p.image_url} alt="Mascot Photo" loading="lazy" />
                        <div className="caption">Mascot 2025</div>
                        <div className="actions">
                            <a href={p.image_url} download="MascotPolaroid.jpg" className="action-link download-btn">DOWNLOAD</a>
                        </div>
                    </div>
                ))}
            </div>

            <style jsx global>{`
                :root {
                    --paper: #fdfbf7;
                    --ink: #2b2b2b;
                    --red: #d32f2f;
                }

                body {
                    /* Corkboard Pattern */
                    background-color: #5c4033;
                    background-image: repeating-linear-gradient(45deg, #6b4c3e 25%, transparent 25%, transparent 75%, #6b4c3e 75%, #6b4c3e), repeating-linear-gradient(45deg, #6b4c3e 25%, #5c4033 25%, #5c4033 75%, #6b4c3e 75%, #6b4c3e);
                    background-position: 0 0, 10px 10px;
                    background-size: 20px 20px;
                    
                    color: var(--ink);
                    font-family: 'Permanent Marker', cursive;
                    margin: 0; padding: 10px;
                    min-height: 100vh;
                }

                h1 {
                    font-size: 2.5em;
                    text-align: center;
                    color: #ffeb3b; 
                    text-shadow: 3px 3px 0px #000;
                    margin-bottom: 5px;
                    transform: rotate(-2deg);
                }

                .subtitle {
                    text-align: center; color: #ddd; margin-bottom: 30px; font-size: 1.0em;
                    text-shadow: 2px 2px 0px #000;
                }

                .gallery {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 40px;
                    padding: 10px;
                    max-width: 1200px;
                    margin: 0 auto;
                }

                .photo-card {
                    background: white;
                    padding: 10px 10px 50px 10px;
                    box-shadow: 5px 5px 10px rgba(0,0,0,0.4);
                    transition: transform 0.3s;
                    position: relative;
                    text-align: center;
                }

                .rotate-left { transform: rotate(-1deg); }
                .rotate-right { transform: rotate(1deg); }

                .photo-card:hover { 
                    transform: scale(1.02); 
                    z-index: 10; 
                    box-shadow: 10px 10px 20px rgba(0,0,0,0.6);
                }

                /* Tape effect */
                .photo-card:before {
                    content: '';
                    position: absolute;
                    top: -10px; left: 50%; transform: translateX(-50%);
                    width: 60px; height: 25px;
                    background: rgba(255,255,255,0.4);
                    border-left: 1px dashed rgba(0,0,0,0.1);
                    border-right: 1px dashed rgba(0,0,0,0.1);
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }

                .photo-card img {
                    width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    filter: contrast(110%); 
                }

                .caption {
                    position: absolute;
                    bottom: 25px; left: 0; right: 0;
                    text-align: center;
                    font-size: 1.0em;
                    color: #555;
                }

                .actions {
                    position: absolute;
                    bottom: 5px; left: 0; right: 0;
                    display: flex; justify-content: space-around;
                    padding: 0 10px;
                }

                .action-link {
                    text-decoration: none;
                    font-size: 0.8em;
                    font-weight: bold;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-family: sans-serif;
                }

                .download-btn { color: #fff; background: #2196F3; }
                
                @media (min-width: 600px) {
                     h1 { font-size: 3.5em; }
                }
            `}</style>
        </div>
    );
}
