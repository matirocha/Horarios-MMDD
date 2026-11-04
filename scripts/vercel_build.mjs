// =============================================================================
// Build de Vercel (lo llama "buildCommand" en vercel.json).
// Copia la página del Prototipo 2 a public/, que es lo único que se publica como sitio.
// El solver se publica aparte, como funciones de Python en api/ (también en vercel.json).
// Si algo falla, el mensaje dice en qué carpeta corrió el build y qué encontró ahí.
// =============================================================================
import { cpSync, existsSync, readdirSync, rmSync, statSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const raiz = resolve(dirname(fileURLToPath(import.meta.url)), '..');   // raíz del repositorio
const origen = join(raiz, 'Prototipos', 'Prototipo 2');
const destino = join(raiz, 'public');
const OMITIR = new Set(['__pycache__', 'README.md', 'servidor.py', 'exportar_datos.py']);

console.log(`Build del Prototipo 2 · carpeta del build: ${process.cwd()} · raíz del repositorio: ${raiz}`);

if (resolve(process.cwd()) !== raiz) {
  console.warn('Aviso: el build no corre en la raíz del repositorio. En Vercel, Settings → Build and Deployment → '
    + 'Root Directory debe quedar vacío; si no, las funciones de api/ (el solver) no se publican.');
}
if (!existsSync(origen)) {
  console.error(`No se encontró la carpeta del prototipo: ${origen}`);
  console.error(`Contenido de ${raiz}: ${readdirSync(raiz).join(', ')}`);
  process.exit(1);
}

rmSync(destino, { recursive: true, force: true });
let archivos = 0;
cpSync(origen, destino, {
  recursive: true,
  filter: ruta => {
    const nombre = basename(ruta);
    if (ruta !== origen && (OMITIR.has(nombre) || nombre.endsWith('.pyc'))) return false;
    if (statSync(ruta).isFile()) archivos += 1;
    return true;
  },
});
console.log(`Listo: ${archivos} archivos en public/ (${readdirSync(destino).join(', ')})`);
