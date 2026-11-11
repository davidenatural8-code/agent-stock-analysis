#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_podcast_kokoro.py — Motor de Síntesis Acústica a 3 Voces (DIRECTOR, ELENA, MARCOS) con Kokoro-ONNX.
Exporta automáticamente el archivo ligero .mp3 (128 kbps) y elimina físicamente el fichero temporal .wav tras la generación.
"""

import os
import re
import sys
import glob
import argparse
import subprocess
import urllib.request
import hashlib
from typing import List, Tuple, Dict

VENV_PY = r"C:\PROJECT\odoo-18.3\venv\Scripts\python.exe"
if os.path.exists(VENV_PY) and "venv" not in sys.prefix.lower():
    sys.exit(subprocess.call([VENV_PY] + sys.argv))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")

import numpy as np
import soundfile as sf
import onnxruntime as rt

try:
    from kokoro_onnx import Kokoro
except ImportError:
    print("ERROR: 'kokoro-onnx' no está instalado. Ejecuta: pip install kokoro-onnx soundfile onnxruntime lameenc imageio-ffmpeg")
    sys.exit(1)

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"


def ensure_kokoro_models(models_dir: str) -> Tuple[str, str]:
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, "kokoro-v1.0.onnx")
    voices_path = os.path.join(models_dir, "voices-v1.0.bin")

    if not os.path.exists(model_path) or os.path.getsize(model_path) < 10_000_000:
        print(f"[Kokoro] Descargando modelo ONNX en {model_path}...")
        urllib.request.urlretrieve(MODEL_URL, model_path)

    if not os.path.exists(voices_path) or os.path.getsize(voices_path) < 1_000_000:
        print(f"[Kokoro] Descargando banco de voces en {voices_path}...")
        urllib.request.urlretrieve(VOICES_URL, voices_path)

    return model_path, voices_path


def build_blended_voices(kokoro: Kokoro) -> Dict[str, np.ndarray]:
    available = set(kokoro.get_voices())

    def get_style(name: str, fallback: str) -> np.ndarray:
        if name in available:
            return kokoro.get_voice_style(name)
        if fallback in available:
            return kokoro.get_voice_style(fallback)
        return kokoro.get_voice_style(list(available)[0])

    es_fem = get_style("ef_dora", "af_bella")
    es_male_1 = get_style("em_alex", "am_michael")
    es_male_2 = get_style("em_santa", "em_alex")

    warm_fem = get_style("af_heart", "ef_dora")
    sharp_male = get_style("am_fenrir", "em_alex")
    deep_baritone = get_style("bm_george", "em_santa")

    voice_director = (0.65 * es_male_2) + (0.23 * es_male_1) + (0.12 * deep_baritone)
    voice_elena = (0.86 * es_fem) + (0.14 * warm_fem)
    voice_marcos = (0.86 * es_male_1) + (0.14 * sharp_male)

    return {
        "DIRECTOR": voice_director,
        "ELENA": voice_elena,
        "MARCOS": voice_marcos,
    }


_ACCENT_RESTORE_MAP = {
    "compania": "compañía", "companias": "compañías", "ano": "año", "anos": "años",
    "diseno": "diseño", "disenado": "diseñado", "redisenar": "rediseñar", "tamano": "tamaño",
    "pequeno": "pequeño", "pequena": "pequeña", "punado": "puñado", "sueno": "sueño",
    "manana": "mañana", "senal": "señal", "senales": "señales", "anadir": "añadir", "anado": "añado",
    "espanol": "español", "espanola": "española", "campana": "campaña", "desempeno": "desempeño",
    "comite": "comité", "sesion": "sesión", "accion": "acción", "valoracion": "valoración",
    "fabricacion": "fabricación", "deposicion": "deposición", "quimica": "química", "quimico": "químico",
    "quimicos": "químicos", "tecnico": "técnico", "tecnica": "técnica", "tecnicos": "técnicos",
    "tecnicas": "técnicas", "tecnologia": "tecnología", "tecnologias": "tecnologías",
    "tecnologico": "tecnológico", "tecnologica": "tecnológica", "margenes": "márgenes",
    "ultimos": "últimos", "ultimas": "últimas", "ultimo": "último", "ultima": "última",
    "perdida": "pérdida", "perdidas": "pérdidas", "optima": "óptima", "optimo": "óptimo",
    "semaforo": "semáforo", "objecion": "objeción", "asimetria": "asimetría", "sintesis": "síntesis",
    "analisis": "análisis", "modulo": "módulo", "modulos": "módulos", "indice": "índice",
    "indices": "índices", "subindices": "subíndices", "multiplo": "múltiplo", "multiplos": "múltiplos",
    "economico": "económico", "economica": "económica", "economias": "economías", "economia": "economía",
    "estrategico": "estratégico", "estrategica": "estratégica", "estrategicas": "estratégicas",
    "bursatil": "bursátil", "capitalizacion": "capitalización", "cotizacion": "cotización",
    "produccion": "producción", "inversion": "inversión", "asignacion": "asignación",
    "ejecucion": "ejecución", "ordenes": "órdenes", "numero": "número", "numeros": "números",
    "pagina": "página", "paginas": "páginas", "catalogo": "catálogo", "atomica": "atómica",
    "atomico": "atómico", "atomos": "átomos", "atomo": "átomo", "oxido": "óxido", "humeda": "húmeda",
    "termica": "térmica", "termicos": "térmicos", "difusion": "difusión", "oxidacion": "oxidación",
    "precision": "precisión", "camara": "cámara", "camaras": "cámaras", "vacio": "vacío",
    "fisica": "física", "nitrogeno": "nitrógeno", "electromagneticos": "electromagnéticos",
    "ceramicos": "cerámicos", "util": "útil", "nanometro": "nanómetro", "nanometros": "nanómetros",
    "nanometrica": "nanométrica", "fijacion": "fijación", "terminos": "términos",
    "absorcion": "absorción", "contratacion": "contratación", "investigacion": "investigación",
    "pekin": "Pekín", "shanghai": "Shanghái", "retencion": "retención", "evolucion": "evolución",
    "explotacion": "explotación", "administracion": "administración", "expansion": "expansión",
    "tematico": "temático", "analiticos": "analíticos", "linea": "línea", "lineas": "líneas",
    "dolares": "dólares", "homologacion": "homologación", "catastrofico": "catastrófico",
    "sustitucion": "sustitución", "basicos": "básicos", "puntuacion": "puntuación",
    "combinacion": "combinación", "validas": "válidas", "criogenico": "criogénico",
    "domestico": "doméstico", "domestica": "doméstica", "domesticos": "domésticos",
    "minimo": "mínimo", "maximo": "máximo", "maxima": "máxima", "maximos": "máximos",
    "bahias": "bahías", "fabricas": "fábricas", "penetracion": "penetración",
    "historicamente": "históricamente", "historicos": "históricos", "automocion": "automoción",
    "inelastica": "inelástica", "politicas": "políticas", "gestion": "gestión",
    "burocratas": "burócratas", "burocraticas": "burocráticas", "ambito": "ámbito",
    "recuperacion": "recuperación", "auditoria": "auditoría", "auditorias": "auditorías",
    "conversion": "conversión", "inflexion": "inflexión", "preparacion": "preparación",
    "multiplicacion": "multiplicación", "razon": "razón", "aceptacion": "aceptación",
    "volumenes": "volúmenes", "certificacion": "certificación", "estanteria": "estantería",
    "criticos": "críticos", "critico": "crítico", "critica": "crítica", "criticas": "críticas",
    "mecanicos": "mecánicos", "aleacion": "aleación", "proximos": "próximos", "proxima": "próxima",
    "reduccion": "reducción", "practica": "práctica", "practico": "práctico",
    "financiacion": "financiación", "refinanciacion": "refinanciación", "direccion": "dirección",
    "calificacion": "calificación", "calificaciones": "calificaciones", "estres": "estrés",
    "probabilisticas": "probabilísticas", "probabilistica": "probabilística", "probabilistico": "probabilístico",
    "manipulacion": "manipulación", "depreciacion": "depreciación", "acumulacion": "acumulación",
    "posicion": "posición", "comoda": "cómoda", "tension": "tensión", "metodologia": "metodología",
    "simulacion": "simulación", "caida": "caída", "contraccion": "contracción", "hipotesis": "hipótesis",
    "desaceleracion": "desaceleración", "automatica": "automática", "prestigio": "prestigio",
    "microelectronico": "microelectrónico", "microelectronica": "microelectrónica",
    "formacion": "formación", "milimetro": "milímetro", "milimetros": "milímetros",
    "cupula": "cúpula", "informacion": "información", "creacion": "creación",
    "meritocratica": "meritocrática", "ingenieria": "ingeniería", "rotacion": "rotación",
    "geopolitica": "geopolítica", "geopolitico": "geopolítico", "geopoliticos": "geopolíticos",
    "deliberacion": "deliberación", "flotacion": "flotación", "corporacion": "corporación",
    "foraneos": "foráneos", "foraneas": "foráneas", "circulacion": "circulación",
    "titulos": "títulos", "titulo": "título", "cuestion": "cuestión", "localizacion": "localización",
    "inyeccion": "inyección", "alimentacion": "alimentación", "norteamerica": "Norteamérica",
    "factorias": "factorías", "colchon": "colchón", "tesoreria": "tesorería", "pulmon": "pulmón",
    "concentracion": "concentración", "dinamica": "dinámica", "macroeconomica": "macroeconómica",
    "vehiculos": "vehículos", "electricos": "eléctricos", "telefonos": "teléfonos", "moviles": "móviles",
    "movil": "móvil", "decada": "década", "reconfiguracion": "reconfiguración",
    "geografica": "geográfica", "digito": "dígito", "vehiculo": "vehículo", "litografia": "litografía",
    "heterogenea": "heterogénea", "vias": "vías", "union": "unión", "progresion": "progresión",
    "desconexion": "desconexión", "anomalo": "anómalo", "corazon": "corazón",
    "triangulacion": "triangulación", "parametros": "parámetros", "intrinseco": "intrínseco",
    "explicito": "explícito", "explicita": "explícita", "estimacion": "estimación",
    "proteccion": "protección", "participes": "partícipes", "implicito": "implícito",
    "panico": "pánico", "division": "división", "divisiones": "divisiones", "analogos": "análogos",
    "peliculas": "películas", "electronicos": "electrónicos", "anomalia": "anomalía",
    "diversificacion": "diversificación", "distribucion": "distribución", "rapida": "rápida",
    "aceleracion": "aceleración", "solidas": "sólidas", "grafico": "gráfico", "patron": "patrón",
    "depuracion": "depuración", "correccion": "corrección", "capitulacion": "capitulación",
    "negociacion": "negociación", "clasico": "clásico", "consideracion": "consideración",
    "vision": "visión", "veintiseis": "veintiséis", "recomendacion": "recomendación",
    "confirmacion": "confirmación", "facturacion": "facturación", "monitorizacion": "monitorización",
    "comprobacion": "comprobación", "confrontacion": "confrontación", "dieciseis": "dieciséis",
    "adaptacion": "adaptación", "digestion": "digestión", "construccion": "construcción",
    "revalorizacion": "revalorización", "amortizaciones": "amortizaciones", "conviccion": "convicción",
    "formulacion": "formulación", "fraccion": "fracción", "teorica": "teórica", "teorico": "teórico",
    "tactico": "táctico", "intradia": "intradía", "rigidamente": "rígidamente", "anatomia": "anatomía",
    "generacion": "generación", "evaluacion": "evaluación", "procedase": "procédase",
    "asiatico": "asiático", "asiatica": "asiática", "autentico": "auténtico", "autentica": "auténtica",
    "unico": "único", "unica": "única", "soberania": "soberanía", "pais": "país", "paises": "países",
    "dias": "días", "dia": "día", "calculo": "cálculo", "razon": "razón", "fundicion": "fundición",
    "maquinas": "máquinas", "maquina": "máquina", "metalicas": "metálicas", "metalicos": "metálicos",
    "dielectricas": "dieléctricas", "logica": "lógica", "masico": "másico",
}


def _restore_word_accents(match: re.Match) -> str:
    w = match.group(0)
    low = w.lower()
    if low not in _ACCENT_RESTORE_MAP:
        return w
    rep = _ACCENT_RESTORE_MAP[low]
    if w.isupper():
        return rep.upper()
    if w[0].isupper():
        return rep[0].upper() + rep[1:]
    return rep


def phonetic_spanish_cleanup(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"[*_`#~|>]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Restauración automática de tildes y eñes si alguna palabra quedó sin acentuar
    text = re.sub(r"\b[A-Za-z]{3,}\b", _restore_word_accents, text)

    replacements = [
        (r"\bCo\.,?\s*Ltd\.?", ""),
        (r"\b1\s+mil\s+800\b", "mil ochocientos"),
        (r"\b1\s+mil\s+0(\d\d)\b", r"mil \1"),
        (r"\b1\s+mil\s+(\d+)\b", r"mil \1"),
        (r"\b(\d+)\s+mil\s+0(\d\d)\b", r"\1 mil \2"),
        (r"\b1H2026\b|\b1H26\b", "primer semestre de dos mil veintiséis"),
        (r"\b2H2026\b|\b2H26\b", "segundo semestre de dos mil veintiséis"),
        (r"\b1H2025\b|\b1H25\b", "primer semestre de dos mil veinticinco"),
        (r"\b2H2025\b|\b2H25\b", "segundo semestre de dos mil veinticinco"),
        (r"\bFY2026E\b|\bFY26E\b", "ejercicio dos mil veintiséis estimado"),
        (r"\bFY2025\b|\bFY25\b", "ejercicio dos mil veinticinco"),
        (r"\bFY2024\b|\bFY24\b", "ejercicio dos mil veinticuatro"),
        (r"\bFY2023\b|\bFY23\b", "ejercicio dos mil veintitrés"),
        (r"\bFY2022\b|\bFY22\b", "ejercicio dos mil veintidós"),
        (r"\bFY2021\b|\bFY21\b", "ejercicio dos mil veintiuno"),
        (r"\bYoY\b", "interanual"),
        (r"\bQoQ\b", "trimestral"),
        (r"\bCAGR\b", "crecimiento anual compuesto"),
        (r"\bbps\b", "puntos básicos"),
        (r"HK\$\s*", "dólares de Hong Kong "),
        (r"\bHKD\b", "dólares de Hong Kong"),
        (r"\bRMB\b|\bCNY\b", "yuanes"),
        (r"US\$\s*|\bUSD\b", "dólares estadounidenses "),
        (r"\bEBITDA\b", "ébitda"),
        (r"\bEBIT\b", "ébit"),
        (r"\bWACC\b", "güac"),
        (r"\bROIC\b", "róic"),
        (r"\bROE\b", "róe"),
        (r"\bROA\b", "róa"),
        (r"\bNOPAT\b|\bNOPLAT\b", "nóplat"),
        (r"\bCapex\b|\bCAPEX\b|\bCapEx\b", "cápex"),
        (r"\bOpEx\b|\bOPEX\b", "ópex"),
        (r"\bCOGS\b", "coste de ventas"),
        (r"\bFCF\b|\bFCFF\b", "flujo de caja libre"),
        (r"\bOCF\b|\bCFO\b", "flujo de caja operativo"),
        (r"\bSOTP\b", "suma de las partes"),
        (r"\bReverse DCF\b", "descuento de flujos inverso"),
        (r"\bDCF\b", "descuento de flujos de caja"),
        (r"\bDSO\b|\bDSRI\b", "días de cobro"),
        (r"\bDPO\b", "días de pago"),
        (r"\bDIO\b", "días de inventario"),
        (r"\bCCC\b", "ciclo de conversión de caja"),
        (r"\bP/E\b|\bPER\b", "múltiplo per"),
        (r"\bEV/EBITDA\b", "valor empresa sobre ébitda"),
        (r"\bP/B\b", "precio sobre valor contable"),
        (r"\bSMIC\b", "esmic"),
        (r"\bCXMT\b", "ChangXin Memory"),
        (r"\bAMEC\b", "ámec"),
        (r"\bALD\b", "deposición de capas atómicas"),
        (r"\b3D NAND\b", "tres de nand"),
        (r"\bDRAM\b", "de ram"),
        (r"\bTSV\b", "vías en silicio"),
        (r"\bBIS\b", "Departamento de Comercio"),
        (r"\bBig Fund III\b", "Gran Fondo Estatal fase tres"),
        (r"\bBig Fund\b", "Gran Fondo Estatal"),
        (r"\bM-Score\b", "índice de Beneish"),
        (r"\bZ-Score\b", "índice Z"),
        (r"\bScorecard\b|\bscorecard\b", "cuadro de mando"),
        (r"\bStop-Loss\b|\bstop-loss\b", "parada de pérdidas"),
        (r"\bspot\b|\bSpot\b", "actual"),
        (r"\bAIDC\b", "centros de datos de inteligencia artificial"),
        (r"\bHVDC\b", "corriente continua de alta tensión"),
        (r"\bBESS\b", "almacenamiento de energía en baterías"),
        (r"\bAMI\b", "medición inteligente"),
        (r"\bSGCC\b", "State Grid"),
        (r"\bCSG\b", "China Southern Power Grid"),
        (r"\bHKEX\b", "Bolsa de Hong Kong"),
        (r"\bHolding\b|\bholding\b", "jólding"),
        (r"\bSpin-off\b|\bspin-off\b", "espín of"),
        (r"\bBuybacks\b|\bbuybacks\b", "recompras de acciones"),
        (r"\bBacklog\b|\bbacklog\b", "cartera de pedidos"),
        (r"\bMoat\b|\bmoat\b", "foso competitivo"),
        (r"\bPeers\b|\bpeers\b", "comparables"),
        (r"\bSpread\b|\bspread\b", "diferencial"),
        (r"\bSell-Side\b|\bsell-side\b", "sel sáid"),
        (r"\bBuy-Side\b|\bbuy-side\b", "bái sáid"),
        (r"\bKill-switch\b|\bkill-switch\b|\bKill-Switch\b", "disparador de salida"),
        (r"\bStress Test\b|\bstress test\b", "test de estrés"),
        (r"\bNAV\b", "patrimonio neto del fondo"),
        (r"\bRSI\b", "erre ese i"),
        (r"\bMACD\b", "mac de"),
        (r"\bMM50\b", "media móvil de cincuenta sesiones"),
        (r"\bMM200\b", "media móvil de doscientas sesiones"),
        (r"\bI\+D\b", "investigación y desarrollo"),
        (r"(\d+)\.(\d+)%", r"\1 coma \2 por ciento"),
        (r"(\d+),(\d+)%", r"\1 coma \2 por ciento"),
        (r"(\d+)%", r"\1 por ciento"),
        (r"(\d+)\.(\d+)x\b", r"\1 coma \2 veces"),
        (r"(\d+)x\b", r"\1 veces"),
    ]

    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)

    text = re.sub(r"\.{2,}", "... ", text)
    text = re.sub(r"\s*[—–-]{1,2}\s*", ", ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_into_prosodic_sentences(text: str, max_chars: int = 420) -> List[str]:
    raw_sentences = re.split(r"(?<=[.!?…])\s+", text.strip())
    chunks: List[str] = []
    current_pack = ""

    for sent in raw_sentences:
        sent = sent.strip()
        if not sent:
            continue
        if len(sent) <= max_chars:
            if len(current_pack) + len(sent) + 1 <= max_chars:
                current_pack = f"{current_pack} {sent}".strip() if current_pack else sent
            else:
                if current_pack:
                    chunks.append(current_pack)
                current_pack = sent
        else:
            if current_pack:
                chunks.append(current_pack)
                current_pack = ""
            subparts = re.split(r"(?<=[;:])\s+|(?<=,)\s+(?=[a-zA-ZáéíóúÁÉÍÓÚñÑ¿¡]{3,})", sent)
            current = ""
            for part in subparts:
                if len(current) + len(part) + 1 <= max_chars:
                    current = f"{current} {part}".strip() if current else part
                else:
                    if current:
                        chunks.append(current)
                    current = part
            if current:
                chunks.append(current)
    if current_pack:
        chunks.append(current_pack)
    return chunks


def compute_dynamic_speed(sentence: str, speaker: str, base_speeds: Dict[str, float], global_scale: float) -> float:
    speed = base_speeds.get(speaker, 1.00) * global_scale
    if "¡" in sentence or "!" in sentence:
        speed += 0.05
    elif "¿" in sentence or "?" in sentence:
        speed += 0.03
    elif "..." in sentence or "…" in sentence:
        speed -= 0.04
    if len(sentence) < 55 and speaker != "DIRECTOR":
        speed += 0.03
    return float(np.clip(speed, 0.80, 1.20))


def trim_and_fade_audio(samples: np.ndarray, sample_rate: int, threshold: float = 0.004) -> np.ndarray:
    if len(samples) == 0:
        return samples
    non_silent = np.where(np.abs(samples) > threshold)[0]
    if len(non_silent) == 0:
        return np.zeros(int(sample_rate * 0.05), dtype=np.float32)
    pad = int(sample_rate * 0.015)
    start = max(0, non_silent[0] - pad)
    end = min(len(samples), non_silent[-1] + pad)
    trimmed = samples[start:end].astype(np.float32)

    fade_len = min(int(sample_rate * 0.008), len(trimmed) // 4)
    if fade_len > 1:
        fade_in = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, fade_len, dtype=np.float32)))
        fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, fade_len, dtype=np.float32)))
        trimmed[:fade_len] *= fade_in
        trimmed[-fade_len:] *= fade_out
    return trimmed


def synthesize_sentence_cached(
    kokoro: Kokoro,
    sent: str,
    voice_vec: np.ndarray,
    spd: float,
    lang: str,
    pause_mult: float,
    cache_dir: str,
    force: bool = False,
) -> Tuple[np.ndarray, int]:
    """Sintetiza una frase prosódica con Kokoro-ONNX empleando caché en disco (.cache_audio/)."""
    sample_rate = 24000
    sent_key = f"{sent}|{spd:.3f}|{lang}|{pause_mult:.3f}"
    sent_hash = hashlib.sha256(sent_key.encode("utf-8")).hexdigest()[:20]
    cache_file = os.path.join(cache_dir, f"{sent_hash}.npy")

    if not force and os.path.exists(cache_file):
        try:
            cached = np.load(cache_file)
            if len(cached) > 0:
                return cached, sample_rate
        except Exception:
            pass

    samples, sample_rate = kokoro.create(
        sent,
        voice=voice_vec,
        speed=spd,
        lang=lang,
        trim=True,
        sentence_pause=0.20 * pause_mult,
        clause_pause=0.10 * pause_mult,
    )
    clean = trim_and_fade_audio(samples, sample_rate)
    try:
        np.save(cache_file, clean)
    except Exception:
        pass
    return clean, sample_rate


def parse_script_file(script_path: str) -> List[Tuple[str, str]]:
    turns: List[Tuple[str, str]] = []
    speaker_regex = re.compile(
        r"^\s*(?:\*\*|#+\s*)?(DIRECTOR|MODERADOR|ELENA|ANALISTA(?:\s+FUNDAMENTAL|\s+SENIOR)?|MARCOS|GESTOR(?:\s+FORENSE)?)(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.+)$",
        re.IGNORECASE,
    )
    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            match = speaker_regex.match(line_str)
            if match:
                raw_spk = match.group(1).upper()
                if raw_spk in ("DIRECTOR", "MODERADOR"):
                    spk = "DIRECTOR"
                elif raw_spk.startswith("ANALISTA") or raw_spk == "ELENA":
                    spk = "ELENA"
                else:
                    spk = "MARCOS"
                dialogue = phonetic_spanish_cleanup(match.group(2))
                if dialogue:
                    turns.append((spk, dialogue))
    return turns


def export_mp3(wav_path: str, mp3_path: str, audio_data: np.ndarray, sample_rate: int) -> None:
    try:
        import lameenc
        pcm16 = (np.clip(audio_data, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(128)
        encoder.set_in_sample_rate(sample_rate)
        encoder.set_channels(1)
        encoder.set_quality(2)
        mp3_bytes = encoder.encode(pcm16) + encoder.flush()
        with open(mp3_path, "wb") as f:
            f.write(mp3_bytes)
        print(f"[MP3] Generado con lameenc: {mp3_path} ({os.path.getsize(mp3_path) / (1024*1024):.2f} MB)")
        return
    except Exception as e:
        print(f"[MP3] Aviso lameenc ({e}), usando respaldo imageio-ffmpeg...")

    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [ffmpeg_exe, "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-b:a", "128k", mp3_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[MP3] Generado con imageio-ffmpeg: {mp3_path} ({os.path.getsize(mp3_path) / (1024*1024):.2f} MB)")
    except Exception as e2:
        print(f"ERROR CRÍTICO al exportar MP3: {e2}")
        sys.exit(1)


def condense_turns_prosodic_sentences(
    turns: List[Tuple[str, str]],
    target_min_chars: int = 42000,
    target_max_chars: int = 60000,
    target_optimal_chars: int = 53000,
) -> Tuple[List[List[str]], List[List[str]], int, int]:
    """
    Divide cada turno en frases prosódicas (split_into_prosodic_sentences) garantizando que
    EL 100% DE LOS TURNOS (Módulo 01 a Módulo 18) se sinteticen sin saltar jamás ninguno.
    - Si el guion completo tiene <= target_max_chars (~60.000 caracteres ≈ 60-63 min), conserva
      el 100% de las frases prosódicas de todos los turnos.
    - Si el guion supera target_max_chars (guiones largos de 12.000-20.000 palabras que superarían
      los 70 minutos), selecciona por rondas (round-robin: frase 1 de cada turno, luego frase 2
      de cada turno, etc.) hasta alcanzar ~target_optimal_chars (~53.000 chars ≈ 52-56 min).
      Al conservar prefijos exactos sentences[:k_i] por turno, reutiliza al 100% la caché .cache_audio.
    Devuelve: (kept_per_turn, extra_per_turn, raw_total_chars, kept_total_chars)
    """
    all_sents: List[List[str]] = []
    for _, dlg in turns:
        sents = split_into_prosodic_sentences(dlg, max_chars=240)
        if not sents and dlg.strip():
            sents = [dlg.strip()]
        all_sents.append(sents)

    raw_total_chars = sum(len(s) for sents in all_sents for s in sents)
    if raw_total_chars <= target_max_chars:
        empty_extras: List[List[str]] = [[] for _ in turns]
        return all_sents, empty_extras, raw_total_chars, raw_total_chars

    n_turns = len(turns)
    keep_counts = [1 if len(all_sents[i]) > 0 else 0 for i in range(n_turns)]
    # Garantizar al menos 2 frases en apertura (primeros 2 turnos) y cierre (últimos 2 turnos)
    for boundary_idx in [0, 1, max(0, n_turns - 2), max(0, n_turns - 1)]:
        if boundary_idx < n_turns and len(all_sents[boundary_idx]) >= 2:
            keep_counts[boundary_idx] = 2

    curr_chars = sum(
        sum(len(s) for s in all_sents[i][: keep_counts[i]])
        for i in range(n_turns)
    )

    max_layers = max((len(s) for s in all_sents), default=1)
    for layer in range(1, max_layers):
        added_any = False
        for i in range(n_turns):
            if curr_chars >= target_optimal_chars:
                break
            if keep_counts[i] == layer and len(all_sents[i]) > layer:
                cand_len = len(all_sents[i][layer])
                if curr_chars + cand_len <= target_max_chars:
                    keep_counts[i] += 1
                    curr_chars += cand_len
                    added_any = True
        if curr_chars >= target_optimal_chars or not added_any:
            break

    kept_per_turn = [all_sents[i][: keep_counts[i]] for i in range(n_turns)]
    extra_per_turn = [all_sents[i][keep_counts[i] :] for i in range(n_turns)]
    return kept_per_turn, extra_per_turn, raw_total_chars, curr_chars


def main():
    parser = argparse.ArgumentParser(description="Generador de Podcast a 3 Voces con Kokoro-ONNX (Cobertura Completa M01-M18, 40-70 min)")
    parser.add_argument("--target-dir", type=str, default=".", help="Carpeta de la empresa <COMPANY_DIR>")
    parser.add_argument("--models-dir", type=str, default="", help="Carpeta de modelos Kokoro")
    parser.add_argument("--script", type=str, default="", help="Ruta opcional al archivo *_PODCAST_GUION.md")
    parser.add_argument("--lang", type=str, default="es", choices=["es", "es-419"])
    parser.add_argument("--speed-scale", type=float, default=1.00)
    parser.add_argument("--min-seconds", type=float, default=float(os.environ.get("PODCAST_MIN_SECONDS", "2460.0")), help="Duración mínima objetivo en segundos (>= 2400s / 40.0 min; por defecto 2460s / 41.0 min)")
    parser.add_argument("--max-seconds", type=float, default=float(os.environ.get("PODCAST_MAX_SECONDS", "4020.0")), help="Duración máxima objetivo en segundos (<= 4200s / 70.0 min; por defecto 4020s / 67.0 min)")
    parser.add_argument("--force", action="store_true", help="Forzar regeneración completa desde cero ignorando caché .npy y .mp3 previo")
    parser.add_argument("--force-rebuild-mp3", action="store_true", help="Reconstruir el archivo .mp3 completo reutilizando las frases ya cacheadas en .cache_audio")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.target_dir)
    shared_candidates = [
        args.models_dir,
        r"C:\PROJECT\Informes\Reports\_shared_engine\kokoro_models",
        r"C:\PROJECT\Informes\_shared_engine\kokoro_models",
        os.path.join(os.path.dirname(target_dir), "_shared_engine", "kokoro_models"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "kokoro_models"),
    ]
    models_dir = next(
        (os.path.abspath(c) for c in shared_candidates if c and os.path.exists(os.path.join(c, "kokoro-v1.0.onnx"))),
        r"C:\PROJECT\Informes\Reports\_shared_engine\kokoro_models",
    )

    script_path = args.script
    if not script_path:
        candidates = glob.glob(os.path.join(target_dir, "*_PODCAST_GUION.md"))
        if not candidates:
            print(f"ERROR: No se encontró ningún archivo *_PODCAST_GUION.md en {target_dir}")
            sys.exit(1)
        script_path = candidates[0]

    prefix = os.path.basename(script_path).replace("_PODCAST_GUION.md", "")
    wav_out = os.path.join(target_dir, f"{prefix}_PODCAST_COMITE.wav")
    mp3_out = os.path.join(target_dir, f"{prefix}_PODCAST_COMITE.mp3")
    manifest_out = os.path.join(target_dir, "podcast_synthesis_manifest.json")

    default_threads = str(min(8, max(2, os.cpu_count() or 4)))
    model_path, voices_path = ensure_kokoro_models(models_dir)
    so = rt.SessionOptions()
    so.intra_op_num_threads = int(os.environ.get("KOKORO_THREADS", default_threads))
    so.inter_op_num_threads = 1
    so.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
    so.add_session_config_entry("session.intra_op.allow_spinning", "0")
    sess = rt.InferenceSession(model_path, sess_options=so, providers=["CPUExecutionProvider"])
    kokoro = Kokoro.from_session(sess, voices_path)
    voices = build_blended_voices(kokoro)

    base_speeds = {"DIRECTOR": 0.96, "ELENA": 1.03, "MARCOS": 0.99}
    turns = parse_script_file(script_path)
    if len(turns) < 10:
        print(f"ERROR: El guion {script_path} solo contiene {len(turns)} turnos válidos.")
        sys.exit(1)

    target_min_sec = max(2400.0, float(args.min_seconds))
    target_max_sec = min(4140.0, max(target_min_sec + 300.0, float(args.max_seconds)))

    existing_audio_path = wav_out if os.path.exists(wav_out) else (mp3_out if os.path.exists(mp3_out) else None)
    if existing_audio_path and not args.force and not args.force_rebuild_mp3:
        try:
            existing_info = sf.info(existing_audio_path)
            existing_dur = float(existing_info.duration)
            manifest_ok = False
            if os.path.exists(manifest_out):
                try:
                    import json
                    with open(manifest_out, "r", encoding="utf-8") as mf:
                        mdata = json.load(mf)
                    if (
                        int(mdata.get("turns_synthesized", 0)) == len(turns)
                        and int(mdata.get("skipped_turns", 999)) == 0
                    ):
                        manifest_ok = True
                except Exception:
                    manifest_ok = False
            if (
                manifest_ok
                and (target_min_sec - 30.0) <= existing_dur <= 4200.0
                and os.path.exists(mp3_out)
                and os.path.getsize(mp3_out) > 20_000_000
            ):
                if os.path.exists(wav_out):
                    try:
                        os.remove(wav_out)
                        print(f"[Kokoro] ({prefix}) Archivo WAV residual eliminado: {wav_out}")
                    except Exception:
                        pass
                print(
                    f"[Kokoro] ({prefix}) MP3 válido existente: {existing_dur/60.0:.2f} min "
                    f"({len(turns)}/{len(turns)} turnos M01-M18 cubiertos). Saltando."
                )
                return
        except Exception as e:
            print(f"[Kokoro] Aviso verificando audio previo ({e}), regenerando...")

    # Calcular presupuesto de caracteres para caer siempre dentro de [target_min_sec, target_max_sec] (~41 a 67 min)
    max_chars_budget = int(target_max_sec * 15.2)
    optimal_chars_budget = int(min(54000, max(44000, ((target_min_sec + target_max_sec) * 0.5) * 16.0)))
    kept_sents, extra_sents, raw_chars, planned_chars = condense_turns_prosodic_sentences(
        turns,
        target_min_chars=int(target_min_sec * 16.2),
        target_max_chars=max_chars_budget,
        target_optimal_chars=optimal_chars_budget,
    )

    print(
        f"[Kokoro] ({prefix}) Sintetizando {len(turns)}/{len(turns)} intervenciones (M01-M18 completos) | "
        f"Caracteres: {planned_chars:,}/{raw_chars:,} | Ventana objetivo: [{target_min_sec/60.0:.1f}m, {target_max_sec/60.0:.1f}m]..."
    )
    audio_segments: List[np.ndarray] = []
    sample_rate = 24000
    total_samples = 0
    cache_dir = os.path.join(target_dir, ".cache_audio")
    os.makedirs(cache_dir, exist_ok=True)

    # Pre-calentamiento paralelo de frases prosódicas no cacheadas (hasta 4 sesiones ONNX en paralelo)
    uncached_tasks = []
    seen_hashes = set()
    for idx_t, (spk_t, _) in enumerate(turns):
        v_vec = voices.get(spk_t, voices["ELENA"])
        for s_t in kept_sents[idx_t]:
            spd_t = compute_dynamic_speed(s_t, spk_t, base_speeds, args.speed_scale)
            h_t = hashlib.sha256(f"{s_t}|{spd_t:.3f}|{args.lang}|1.000".encode("utf-8")).hexdigest()[:20]
            c_file = os.path.join(cache_dir, f"{h_t}.npy")
            if h_t not in seen_hashes and (args.force or not os.path.exists(c_file)):
                seen_hashes.add(h_t)
                uncached_tasks.append((s_t, v_vec, spd_t))

    sent_workers = int(os.environ.get("KOKORO_SENTENCE_WORKERS", "4"))
    if len(uncached_tasks) > 4 and sent_workers > 1:
        from concurrent.futures import ThreadPoolExecutor
        import threading
        print(f"  [Kokoro] Pre-sintetizando {len(uncached_tasks)} frases nuevas en paralelo (workers={sent_workers})...", flush=True)
        tls = threading.local()

        def _get_worker_kokoro():
            if not hasattr(tls, "k"):
                so_w = rt.SessionOptions()
                so_w.intra_op_num_threads = max(2, (os.cpu_count() or 8) // sent_workers)
                so_w.inter_op_num_threads = 1
                so_w.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
                so_w.add_session_config_entry("session.intra_op.allow_spinning", "0")
                sess_w = rt.InferenceSession(model_path, sess_options=so_w, providers=["CPUExecutionProvider"])
                tls.k = Kokoro.from_session(sess_w, voices_path)
            return tls.k

        def _synth_task(item):
            s_i, v_i, spd_i = item
            k_inst = _get_worker_kokoro()
            synthesize_sentence_cached(k_inst, s_i, v_i, spd_i, args.lang, 1.0, cache_dir, args.force)

        with ThreadPoolExecutor(max_workers=sent_workers) as pool:
            list(pool.map(_synth_task, uncached_tasks))

    turns_synthesized_count = 0
    chars_spoken_so_far = 0

    for idx, (speaker, _dialogue) in enumerate(turns):
        curr_sec = total_samples / float(sample_rate)
        sentences = list(kept_sents[idx])

        # Ajuste dinámico suave en el último tercio si hiciera falta para garantizar [target_min_sec, target_max_sec]
        rem_kept_chars = max(1, sum(sum(len(s) for s in kept_sents[j]) for j in range(idx, len(turns))))
        obs_rate = (chars_spoken_so_far / curr_sec) if (curr_sec > 300.0 and chars_spoken_so_far > 4000) else 16.5
        obs_rate = float(np.clip(obs_rate, 14.0, 19.0))
        projected_final_sec = curr_sec + (rem_kept_chars / obs_rate)

        eff_scale = args.speed_scale
        pause_mult = 1.0

        # Si proyectamos quedar por debajo del mínimo y este turno tiene frases extra recortadas, restaurarlas a velocidad 1.0
        if projected_final_sec < (target_min_sec + 45.0) and extra_sents[idx]:
            while extra_sents[idx] and projected_final_sec < (target_min_sec + 90.0):
                restored = extra_sents[idx].pop(0)
                sentences.append(restored)
                rem_kept_chars += len(restored)
                projected_final_sec = curr_sec + (rem_kept_chars / obs_rate)

        # Si el guion completo es corto y aun con todas las frases proyecta < target_min_sec, ralentizar suavemente
        if projected_final_sec < (target_min_sec + 20.0):
            sec_needed = max(10.0, (target_min_sec + 30.0) - curr_sec)
            est_sec_normal = rem_kept_chars / obs_rate
            eff_scale = float(np.clip(args.speed_scale * (est_sec_normal / max(1.0, sec_needed * 1.04)), 0.82, 1.00))
            pause_mult = float(np.clip(sec_needed / max(1.0, est_sec_normal), 1.0, 1.32))
        # Si proyectamos acercarnos al techo de 70 min (target_max_sec), quedarnos con la frase principal del turno
        elif projected_final_sec > target_max_sec and len(sentences) > 1 and idx < len(turns) - 2:
            sentences = sentences[:1]

        voice_vec = voices.get(speaker, voices["ELENA"])
        for s_idx, sent in enumerate(sentences):
            spd = compute_dynamic_speed(sent, speaker, base_speeds, eff_scale)
            clean_samples, sample_rate = synthesize_sentence_cached(
                kokoro, sent, voice_vec, spd, args.lang, pause_mult, cache_dir, args.force
            )
            audio_segments.append(clean_samples)
            total_samples += len(clean_samples)
            chars_spoken_so_far += len(sent)
            if s_idx < len(sentences) - 1:
                intra_pause = (0.26 if sent.endswith("...") else (0.18 if sent.endswith(("?", "!")) else 0.13)) * pause_mult
                p_arr = np.zeros(int(sample_rate * intra_pause), dtype=np.float32)
                audio_segments.append(p_arr)
                total_samples += len(p_arr)

        turns_synthesized_count += 1
        if idx < len(turns) - 1:
            next_speaker, next_text = turns[idx + 1]
            turn_pause = (0.18 if (len(next_text) < 110 or next_text.startswith(("¡", "¿"))) else (0.38 if next_speaker == "DIRECTOR" else 0.28)) * pause_mult
            p_arr = np.zeros(int(sample_rate * turn_pause), dtype=np.float32)
            audio_segments.append(p_arr)
            total_samples += len(p_arr)

        if (idx + 1) % 25 == 0 or idx == len(turns) - 1:
            print(
                f"  [Kokoro] Progreso: turno {idx+1}/{len(turns)} | "
                f"Audio acumulado: {(total_samples/sample_rate)/60.0:.2f} min",
                flush=True,
            )

    full_audio = np.concatenate(audio_segments)
    full_audio = np.tanh(full_audio * 1.15).astype(np.float32)
    peak = np.max(np.abs(full_audio))
    if peak > 0:
        full_audio = (full_audio / peak) * 0.84

    final_dur_sec = len(full_audio) / float(sample_rate)
    print(
        f"[Kokoro] ({prefix}) Duración final MP3: {final_dur_sec:.1f}s ({final_dur_sec/60.0:.2f} min) | "
        f"Turnos sintetizados: {turns_synthesized_count}/{len(turns)} (0 saltados)"
    )
    sf.write(wav_out, full_audio, sample_rate)
    export_mp3(wav_out, mp3_out, full_audio, sample_rate)
    if os.path.exists(wav_out):
        try:
            os.remove(wav_out)
            print(f"[Kokoro] ({prefix}) Fichero temporal WAV borrado físicamente tras generar el MP3: {wav_out}")
        except Exception as e:
            print(f"[Kokoro] Aviso al borrar el fichero WAV {wav_out}: {e}")

    try:
        import json
        manifest_payload = {
            "prefix": prefix,
            "script_file": os.path.basename(script_path),
            "mp3_file": os.path.basename(mp3_out),
            "total_turns_in_script": len(turns),
            "turns_synthesized": turns_synthesized_count,
            "skipped_turns": len(turns) - turns_synthesized_count,
            "first_turn_idx": 0,
            "last_turn_idx": len(turns) - 1,
            "raw_script_chars": raw_chars,
            "spoken_chars": chars_spoken_so_far,
            "duration_seconds": round(final_dur_sec, 2),
            "duration_minutes": round(final_dur_sec / 60.0, 2),
            "min_seconds_target": target_min_sec,
            "max_seconds_target": target_max_sec,
            "full_module_coverage_m01_m18": (turns_synthesized_count == len(turns)),
        }
        with open(manifest_out, "w", encoding="utf-8") as mf:
            json.dump(manifest_payload, mf, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Kokoro] Aviso guardando manifest de síntesis: {e}")


if __name__ == "__main__":
    main()
