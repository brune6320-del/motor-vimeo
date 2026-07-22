const express = require('express');
const cors = require('cors');
const youtubedl = require('youtube-dl-exec');

const app = express();
app.use(cors());
app.use(express.json());

app.post('/api/getVideo', async (req, res) => {
    const { videoUrl, password } = req.body;

    if (!videoUrl) {
        return res.status(400).json({ error: "Falta la URL del video." });
    }

    try {
        console.log(`[+] Procesando extracción para: ${videoUrl}`);
        
        const flags = {
            dumpSingleJson: true,
            noWarnings: true,
            noCallHome: true,
            noCheckCertificate: true,
            youtubeSkipDashManifest: true
        };

        if (password) {
            flags.videoPassword = password;
        }

        const output = await youtubedl(videoUrl, flags);

        const formatosMp4 = output.formats
            .filter(f => f.ext === 'mp4' && f.vcodec !== 'none')
            .map(f => ({
                calidad: f.format_note || (f.height ? `${f.height}p` : 'Desconocida'),
                resolucion: f.width && f.height ? `${f.width}x${f.height}` : 'N/A',
                link: f.url
            }));

        const formatosUnicos = [];
        const resolucionesVistas = new Set();
        
        for (const formato of formatosMp4.reverse()) {
            if (!resolucionesVistas.has(formato.resolucion)) {
                resolucionesVistas.add(formato.resolucion);
                formatosUnicos.push(formato);
            }
        }

        return res.json({
            success: true,
            titulo: output.title,
            descargas: formatosUnicos.reverse()
        });

    } catch (error) {
        if (error.message.toLowerCase().includes('password')) {
            return res.status(403).json({ error: "El video requiere contraseña o la contraseña es incorrecta." });
        }
        if (error.message.toLowerCase().includes('not found') || error.message.toLowerCase().includes('404')) {
            return res.status(404).json({ error: "Video no encontrado o enlace inválido." });
        }
        return res.status(500).json({ error: "Error procesando el video." });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`[+] Servidor escuchando en puerto ${PORT}`);
});
