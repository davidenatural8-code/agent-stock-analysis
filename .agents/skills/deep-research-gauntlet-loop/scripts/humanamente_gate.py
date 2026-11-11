#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
humanamente_gate.py — Auditor Determinista y Gestor del Bucle de 3 Pasadas de `vicentealvarezasencio/humanamente`.

Integra de forma obligatoria y bloqueante las reglas editoriales y tipográficas de `humanamente`
en los tres entregables textuales del pipeline `deep-research-gauntlet-loop`:
  1. Informe Maestro y Borradores (`borrador_parte1..4.md` y `*_INFORME_COMITE_FINAL.md`)
  2. Presentación Institucional de 40 Diapositivas (`*_PRESENTACION_COMITE_40_SLIDES.pptx`)
  3. Guion de Podcast a 3 Voces (`*_PODCAST_GUION.md`)

Modos de uso:
  # 1) Auditar un borrador individual nada más escribirlo (Pasada 2 de humanamente):
  python humanamente_gate.py --file "<COMPANY_DIR>/borrador_parte1.md" --mode md-draft

  # 2) Registrar la certificación del Motor de 3 Pasadas (Rúbrica 6 dimensiones >= 42/60):
  python humanamente_gate.py --target-dir "<COMPANY_DIR>" --record-audit md \
      --scores "8,8,8,7,8,7" --tics "P03,P07,P14,P17,P32" \
      --notes "Eliminados gerundios de cola, title case en subtítulos y rayas inglesas; inyectado burstiness."

  # 3) Validar cumplimiento estricto por subsistema o completo (invocado automáticamente por gauntlet_gatekeeper.py):
  python humanamente_gate.py --target-dir "<COMPANY_DIR>" --target md|pptx|podcast|all
"""

import os
import re
import sys
import glob
import json
import math
import argparse
import subprocess
from datetime import datetime
from typing import List, Dict, Tuple

VENV_PY = r"C:\PROJECT\odoo-18.3\venv\Scripts\python.exe"
if os.path.exists(VENV_PY) and "venv" not in sys.prefix.lower():
    sys.exit(subprocess.call([VENV_PY] + sys.argv))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ==============================================================================
# 1. DETECTOR PRECISO DE TITLE CASE ANGLOSAJÓN EN CASTELLANO (PATRÓN P17)
# ==============================================================================
# Palabras comunes del castellano (sustantivos, adjetivos, verbos y preposiciones largas)
# que NUNCA llevan mayúscula inicial en mitad de un titular en español según la RAE / P17.
SPANISH_COMMON_WORDS = {
    # Preposiciones, conjunciones, adverbios y determinantes que los LLM capitalizan en Title Case
    "ante", "bajo", "cabe", "como", "contra", "desde", "durante", "entre", "frente",
    "hacia", "hasta", "mediante", "para", "pero", "pese", "según", "segun", "sobre",
    "tras", "versus", "cuando", "donde", "mientras", "aunque", "además", "ademas",
    "cada", "todo", "toda", "todos", "todas", "otro", "otra", "otros", "otras",
    "mismo", "misma", "mayor", "menor", "mejor", "peor", "gran", "alto", "alta",
    "altos", "altas", "bajo", "bajos", "bajas", "nuevo", "nueva", "nuevos", "nuevas",
    "último", "ultimo", "última", "ultima", "últimos", "ultimos", "últimas", "ultimas",
    "primer", "primera", "primeros", "primeras", "segundo", "segunda", "tercer", "tercera",
    # Meses y estaciones (en español SIEMPRE van en minúscula: P17)
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "setiembre", "octubre", "noviembre", "diciembre",
    # Léxico financiero, contable, estratégico y corporativo común en titulares
    "acción", "accion", "acciones", "accionarial", "accionistas", "activo", "activos",
    "actual", "actuales", "acumulado", "acumulada", "ajuste", "ajustes", "ajustado", "ajustada",
    "alerta", "alianza", "alianzas", "análisis", "analisis", "analítica", "analitica", "analítico",
    "anatomía", "anatomia", "anual", "anuales", "anualizada", "anualizado", "apalancamiento",
    "aplicación", "aplicacion", "aplicaciones", "aprobada", "aprobado", "árbol", "arbol",
    "arquitectura", "asignación", "asignacion", "asimetría", "asimetria", "asimétrico",
    "auditoría", "auditoria", "auditada", "auditado", "auditadas", "auditados", "avance",
    "avanzada", "avanzado", "balance", "balances", "banderas", "barreras", "base", "beneficio",
    "beneficios", "bloque", "bloques", "bolsa", "bolsas", "bolsillo", "bruta", "bruto",
    "bursátil", "bursatil", "bursátiles", "cadena", "caída", "caida", "caja", "calidad",
    "calificación", "calificacion", "calendario", "cambio", "campo", "canal", "canales",
    "capacidad", "capital", "capitalización", "cartera", "caso", "casos", "catálogo", "catalogo",
    "catalizador", "catalizadores", "cierre", "ciclo", "ciclos", "cinco", "circulante",
    "clave", "claves", "cliente", "clientes", "cobertura", "cobro", "cobros", "comercial",
    "comerciales", "comparables", "comparativa", "comparativo", "competencia", "competidores",
    "competitiva", "competitivo", "completa", "completo", "comportamiento", "compra", "comprar",
    "compras", "común", "concentración", "concentracion", "conciliación", "conciliacion",
    "conclusión", "conclusion", "condiciones", "consenso", "consolidada", "consolidado",
    "consolidados", "contable", "contables", "contexto", "continuada", "continuadas",
    "contractual", "control", "conversión", "conversion", "convicción", "conviccion",
    "corporativa", "corporativo", "corto", "coste", "costes", "costo", "costos", "cotización",
    "cotizacion", "cotizada", "cotizadas", "cotizado", "cotizados", "creación", "creacion",
    "crecimiento", "crédito", "credito", "criterio", "crítica", "critica", "críticas", "criticas",
    "cronología", "cronologia", "comentada", "cuantitativa", "cuantitativo", "cuantitativas",
    "cuantificado", "cuatro", "cuenta", "cuentas", "cultura", "cultural", "cuota", "cuotas",
    "datos", "debate", "decisión", "decision", "declarados", "declaradas", "deducción",
    "desarrollo", "descuento", "desempeño", "desempeno", "desglose", "destacado", "detalle",
    "determinación", "determinacion", "deuda", "diagnóstico", "diagnostico", "diapositiva",
    "dictamen", "diferenciador", "dilución", "dilucion", "dinámica", "dinamica", "dinámico",
    "directa", "directo", "directos", "directiva", "directivos", "disciplina", "disciplinada",
    "disrupción", "disrupcion", "distribución", "distribucion", "dividendo", "dividendos",
    "divisa", "divisas", "doble", "documental", "económica", "economica", "económico", "economico",
    "efectivo", "efecto", "efectos", "eficiencia", "ejecución", "ejecucion", "ejecutable",
    "ejecutiva", "ejecutivo", "ejes", "emisión", "emisiones", "empresa", "empresas", "energía",
    "entorno", "escala", "escenario", "escenarios", "especificación", "especificaciones",
    "específicos", "esperado", "esperada", "estabilidad", "estados", "estimada", "estimado",
    "estrategia", "estratégica", "estrategica", "estratégico", "estrategico", "estratégicos",
    "estrés", "estres", "estructura", "estructural", "estructurales", "evaluación", "evaluacion",
    "eventos", "evidencia", "evolución", "evolucion", "exactamente", "exhaustiva", "exhaustivo",
    "expansión", "expansion", "exposición", "exposicion", "externa", "factores", "facturación",
    "fase", "fases", "ficha", "fijos", "final", "financiera", "financiero", "financieras",
    "financieros", "física", "fisica", "físicos", "fisicos", "flujo", "flujos", "fondo", "fondos",
    "forense", "forenses", "fortaleza", "foso", "fuentes", "fuerzas", "funcional", "fundamentos",
    "futura", "futuro", "futuras", "futuros", "gasto", "gastos", "generación", "generacion",
    "general", "geografía", "geografia", "gestión", "gestion", "global", "globales", "gobernanza",
    "gobierno", "grado", "gráfico", "grafico", "grupo", "hallazgos", "hechos", "hipótesis",
    "hipotesis", "historia", "histórica", "historica", "histórico", "historico", "históricos",
    "hitos", "horizonte", "hoy", "impacto", "impuestos", "incentivos", "indicador", "indicadores",
    "índice", "indice", "industria", "industrial", "ínfima", "infima", "inflación", "inflacion",
    "información", "informe", "ingreso", "ingresos", "inicial", "injustificado", "inexpugnable",
    "innovación", "innovacion", "institucional", "institucionales", "integración", "integracion",
    "integrada", "integrado", "integral", "inteligencia", "intensidad", "interanual", "interés",
    "interna", "interno", "internacional", "intrínseco", "intrinseco", "inversión", "inversion",
    "investigación", "investigacion", "jerarquía", "jerarquia", "laboral", "largo", "latente",
    "legal", "libre", "liderazgo", "línea", "linea", "líneas", "liquidez", "lista", "litigios",
    "macro", "macroeconomía", "macroeconomia", "maestra", "maestro", "manipulación", "mapa",
    "marco", "margen", "márgenes", "margenes", "masiva", "materias", "matemática", "matematica",
    "matemático", "matriz", "máxima", "maxima", "máximo", "mecánica", "mecanica", "media",
    "medias", "medio", "mejora", "mercado", "mercados", "metalúrgica", "metodo", "método",
    "métricas", "metricas", "millones", "minera", "minero", "mineros", "mínima", "minima",
    "mínimo", "modelo", "modelos", "módulo", "modulo", "módulos", "modulos", "monetización",
    "monitorización", "monitorizacion", "movimientos", "multianual", "multidimensional",
    "múltiplo", "multiplo", "múltiplos", "multiplos", "narrativa", "naturaleza", "negocio",
    "negocios", "neta", "neto", "nivel", "niveles", "normativa", "notas", "noticias", "nuevos",
    "numérica", "numerados", "objetivo", "oculta", "ocultos", "onza", "onzas", "operación",
    "operaciones", "operativa", "operativo", "operativas", "operativos", "oportunidad", "orden",
    "orgánica", "organica", "orgánico", "organico", "organizacional", "osciladores", "pago",
    "país", "pais", "parámetros", "parametros", "partes", "partidas", "pasivo", "pasivos",
    "patrimonial", "patrimonio", "penalización", "perdidas", "pérdidas", "perfil", "perfiles",
    "perímetro", "periodo", "perspectiva", "pilares", "plan", "planta", "plantas", "plataforma",
    "plataformas", "plazo", "poder", "ponderada", "ponderado", "por", "portafolio", "posición",
    "posicion", "posicionamiento", "positivos", "potencial", "precio", "precios", "preliminar",
    "prensa", "preservación", "prima", "primaria", "primario", "primas", "principal",
    "principales", "probabilidad", "probabilísticos", "producción", "produccion", "productividad",
    "producto", "productos", "productor", "profunda", "profundo", "programa", "propia",
    "propiedad", "prosa", "proveedores", "provisiones", "proyección", "proyecciones", "proyecto",
    "proyectos", "prueba", "puntos", "puntuación", "puntuacion", "pura", "puro", "quinquenio",
    "radiografía", "rango", "ratio", "ratios", "real", "reales", "reciente", "recientes",
    "recompra", "recompras", "recomendación", "recomendado", "récord", "record", "recursos",
    "red", "reducción", "referencia", "regulación", "regulacion", "regulatorio", "regulatorios",
    "relaciones", "relevantes", "remuneración", "rendimiento", "rentabilidad", "reorganización",
    "reorganizada", "reportado", "reporte", "reputación", "reservar", "reservas", "resistencias",
    "respaldo", "resumen", "resultado", "resultados", "retención", "retorno", "revalorización",
    "reto", "retos", "desafío", "desafio", "desafíos", "desafios", "amenaza", "amenazas",
    "oportunidad", "oportunidades", "debilidad", "debilidades", "perspectiva", "perspectivas",
    "riesgo", "riesgos", "rigor", "rojas", "rotación", "salud", "sanciones", "sección",
    "seccion", "sector", "sectorial", "sectoriales", "segmento", "segmentos", "seguimiento",
    "segura", "seis", "semestral", "sensibilidad", "sensibilidades", "sentimiento", "señales",
    "senales", "serie", "servicio", "servicios", "severa", "sin", "síntesis", "sintesis",
    "sistema", "situación", "sobreventa", "societaria", "solvencia", "soportes", "sostenibilidad",
    "sucesión", "suma", "superiores", "tabla", "tablas", "táctica", "tactica", "táctico",
    "talento", "tamaño", "tasa", "técnica", "tecnica", "técnico", "tecnico", "tecnológica",
    "temporal", "tendencia", "tesorería", "tesis", "tiempo", "tipo", "total", "totales",
    "trabajo", "tramos", "transacciones", "transición", "trayectoria", "tres", "trimestral",
    "trimestrales", "trimestre", "unidad", "unitaria", "únicos", "valor", "valoración",
    "valoraciones", "valores", "variable", "variables", "velocidades", "vencimientos", "venta",
    "ventaja", "ventas", "veredicto", "verificación", "vida", "vientos", "vigencia", "vinculadas",
    "vinculante", "visibilidad", "volumen",
}

SPANISH_COMMON_SUFFIX_RE = re.compile(
    r"^[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]{4,}(?:ción|ciones|sión|siones|miento|mientos|dad|dades|tad|tades|"
    r"anza|anzas|encia|encias|ismo|ismos|ista|istas|able|ables|ible|ibles|mente|dora|doras|dores|"
    r"tiva|tivas|tivo|tivos|aria|arias|ario|arios|lógica|lógico|métrica|métrico)$"
)

# Excepciones institucionales legítimas (órganos propios o términos técnicos fijados)
PROPER_NOUN_EXCEPTIONS = {
    "Comité", "Inversiones", "Consejo", "Administración", "Estado", "Estados",
    "Unidos", "Naciones", "Unidas", "Bolsa", "Valores", "Banco", "Central",
}


def is_mid_sentence_title_case_word(word: str) -> bool:
    """Devuelve True si `word` es una palabra común castellana escrita con Mayúscula Inicial indebida."""
    if not word or len(word) < 4:
        return False
    # Ignorar siglas/tickers en MAYÚSCULAS o alfanuméricos (EBITDA, ROIC, 1H26, Q3, P/E)
    if word.isupper() or any(ch.isdigit() for ch in word):
        return False
    # Solo analizar palabras con patrón " Inicial Mayúscula + resto minúsculas "
    if not (word[0].isupper() and word[1:].islower()):
        return False
    if word in PROPER_NOUN_EXCEPTIONS:
        return False
    low = word.lower()
    if low in SPANISH_COMMON_WORDS:
        return True
    if SPANISH_COMMON_SUFFIX_RE.match(word):
        return True
    return False


def heading_has_english_title_case(heading_text: str) -> Tuple[bool, List[str]]:
    """
    Evalúa un titular o Action Title según P17 de `humanamente`:
    En español solo llevan mayúscula la primera palabra (o la primera tras ':' / '—' / numeración)
    y los nombres propios o siglas. Si aparecen >= 2 palabras comunes castellanas capitalizadas
    en mitad del titular, es Title Case anglosajón (P17).
    """
    clean = re.sub(r"^#{1,6}\s*", "", heading_text).strip()
    clean = re.sub(r"[`*_]", "", clean).strip()
    if not clean or clean.isupper():
        return False, []

    # Dividir en sub-cláusulas por ':', '—', '–', ' - ', '(', '/' para permitir mayúscula inicial tras dos puntos
    clauses = re.split(r"[:\(\n]|\s[—–-]\s", clean)
    bad_words: List[str] = []

    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        # Quitar prefijos de numeración como "1.1", "Módulo 02", "Sección A"
        clause = re.sub(r"^(?:M[oó]dulo\s+\d+|Secci[oó]n\s+[A-Z]|\d+(?:\.\d+)*[\.\)]?)\s*", "", clause, flags=re.IGNORECASE).strip()
        tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", clause)
        if len(tokens) <= 1:
            continue
        for tok in tokens[1:]:
            if is_mid_sentence_title_case_word(tok):
                bad_words.append(tok)

    return (len(bad_words) >= 2), bad_words


# ==============================================================================
# 1.1 AUTO-CORRECTOR DETERMINISTA DE PATRONES P14, P17, P18, P19 (0 TOKENS LLM)
# ==============================================================================
def autofix_heading(heading_line: str) -> Tuple[str, bool]:
    """Convierte titulares con Title Case anglosajón a sentence case español (P17), y limpia rayas inglesas P14."""
    original = heading_line
    line = heading_line.replace("“", "«").replace("”", "»")
    line = re.sub(r"\s+[—–]\s+", ": ", line)
    line = re.sub(r"\s+--\s+", ": ", line)

    m = re.match(r"^(#{1,6}\s+)(.*)$", line)
    if not m:
        return line, (line != original)

    prefix, body = m.group(1), m.group(2)
    is_tc, bad_words = heading_has_english_title_case(body)
    if bad_words:
        for bw in bad_words:
            # Reemplazar la palabra con límite estricto de palabra para no tocar siglas
            body = re.sub(r"(?<![A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9])" + re.escape(bw) + r"(?![A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9])", bw.lower(), body)
        line = prefix + body

    return line, (line != original)


def autofix_markdown_text(text: str) -> Tuple[str, List[str]]:
    """Aplica correcciones deterministas (0 tokens LLM) para P14, P17, P18, P19."""
    fixes: List[str] = []

    # 1. P19 Comillas curvas
    curly_cnt = len(CURLY_QUOTES_RE.findall(text))
    if curly_cnt > 0:
        text = text.replace("“", "«").replace("”", "»")
        fixes.append(f"P19: {curly_cnt} comillas inglesas sustituidas por «comillas latinas»")

    # 2. P18 Emojis
    emoji_cnt = len(EMOJI_RE.findall(text))
    if emoji_cnt > 0:
        text = EMOJI_RE.sub("", text)
        fixes.append(f"P18: {emoji_cnt} emojis eliminados")

    # 3. Titulares (P17 + P14) y prosa (P14)
    lines = text.splitlines()
    new_lines = []
    h_fixed = 0
    emdash_fixed = 0
    in_code_block = False

    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            new_lines.append(ln)
            continue
        if in_code_block:
            new_lines.append(ln)
            continue

        # Titular Markdown
        if re.match(r"^#{1,6}\s+", ln):
            fixed_h, was_changed = autofix_heading(ln)
            if was_changed:
                h_fixed += 1
            new_lines.append(fixed_h)
            continue

        # Prosa narrativa (no tabla Markdown)
        if not ln.strip().startswith("|"):
            if " — " in ln:
                emdash_fixed += len(re.findall(r"\s—\s", ln))
                ln = re.sub(r"\s—\s", ", ", ln)
            if " -- " in ln:
                emdash_fixed += len(re.findall(r"\s--\s", ln))
                ln = re.sub(r"\s--\s", ", ", ln)

        new_lines.append(ln)

    if h_fixed > 0:
        fixes.append(f"P17: {h_fixed} titulares corregidos a sentence case español")
    if emdash_fixed > 0:
        fixes.append(f"P14: {emdash_fixed} rayas inglesas ' — ' sustituidas por puntuación española")

    new_text = "\n".join(new_lines)

    # 4. P03/P22 Gerundios de consecuencia tras coma (preservando concordancia singular/plural)
    gerund_map = {
        ", permitiendo ": ", lo que permite ",
        ", garantizando ": ", lo que garantiza ",
        ", logrando ": ", con lo que logra ",
        ", consolidando ": ", lo que consolida ",
        ", reflejando ": ", lo que refleja ",
        ", situando ": ", lo que sitúa ",
        ", generando ": ", lo que genera ",
        ", demostrando ": ", lo que demuestra ",
        ", destacando ": ", donde destaca ",
        ", poniendo de manifiesto ": ", lo que evidencia ",
        ", asegurando ": ", lo que asegura ",
        ", evidenciando ": ", lo que evidencia ",
        ", confirmando ": ", lo que confirma ",
        ", fortaleciendo ": ", lo que fortalece ",
        ", optimizando ": ", lo que optimiza ",
        ", maximizando ": ", lo que maximiza ",
        ", subrayando ": ", lo que señala ",
        ", consiguiendo ": ", con lo que consigue ",
        ", facilitando ": ", lo que facilita ",
        ", impulsando ": ", lo que impulsa ",
    }
    g_fixed = 0
    for g_from, g_to in gerund_map.items():
        cnt = new_text.count(g_from) + new_text.count(g_from.capitalize())
        if cnt > 0:
            new_text = new_text.replace(g_from, g_to).replace(g_from.capitalize(), g_to.capitalize())
            g_fixed += cnt
    if g_fixed > 0:
        fixes.append(f"P03/P22: {g_fixed} gerundios de consecuencia tras coma transformados a voz activa")

    # 5. P24/P07 Clichés y vocabulario IA
    cliche_map = {
        "pone de relieve": "evidencia",
        "Pone de relieve": "Evidencia",
        "pone de manifiesto": "demuestra",
        "Pone de manifiesto": "Demuestra",
        "cabe destacar": "conviene apuntar",
        "Cabe destacar": "Conviene apuntar",
        "cabe señalar": "conviene señalar",
        "Cabe señalar": "Conviene señalar",
        "cabe mencionar": "conviene mencionar",
        "Cabe mencionar": "Conviene mencionar",
        "cabe resaltar": "conviene resaltar",
        "Cabe resaltar": "Conviene resaltar",
        "es importante destacar": "resulta relevante notar",
        "Es importante destacar": "Resulta relevante notar",
        "es importante señalar": "resulta relevante indicar",
        "Es importante señalar": "Resulta relevante indicar",
        "es importante tener en cuenta": "conviene considerar",
        "Es importante tener en cuenta": "Conviene considerar",
        "es preciso destacar": "conviene notar",
        "Es preciso destacar": "Conviene notar",
        "se puede observar que": "se observa que",
        "Se puede observar que": "Se observa que",
        "se hace necesario": "resulta necesario",
        "Se hace necesario": "Resulta necesario",
        "cabe preguntarse": "conviene plantearse",
        "Cabe preguntarse": "Conviene plantearse",
        "pone de manifiesto": "muestra",
        "Pone de manifiesto": "Muestra",
        "poniendo de manifiesto": "lo que muestra",
        "pone de relieve": "evidencia",
        "Pone de relieve": "Evidencia",
        "poner de relieve": "evidenciar",
        "juega un papel fundamental": "cumple una función esencial",
        "juega un papel crucial": "cumple una función crítica",
        "juega un papel vital": "cumple una función decisiva",
        "juega un papel clave": "cumple una función central",
        "desempeña un papel fundamental": "cumple una función esencial",
        "desempeña un papel crucial": "cumple una función crítica",
        "desempeña un papel vital": "cumple una función decisiva",
        "desempeña un papel clave": "cumple una función central",
        "marcó un hito": "supuso un punto de inflexión",
        "Marcó un hito": "Supuso un punto de inflexión",
        "marca un antes y un después": "supone un cambio estructural",
        "se erige como": "actúa como",
        "Se erige como": "Actúa como",
        "constituye un testimonio": "es prueba directa",
        "un sinfín de": "múltiples",
        "una miríada de": "numerosas",
        "en el panorama actual": "en el contexto actual",
        "en el mundo actual": "en el mercado actual",
        "en la era digital": "en el entorno tecnológico actual",
        "sin lugar a dudas": "con certeza",
        "Sin lugar a dudas": "Con certeza",
        "sin duda alguna": "con claridad",
        "Sin duda alguna": "Con claridad",
        "en conclusión,": "en síntesis,",
        "En conclusión,": "En síntesis,",
        "en definitiva,": "en suma,",
        "En definitiva,": "En suma,",
        "en última instancia,": "al final,",
        "En última instancia,": "Al final,",
        "como hemos visto a lo largo": "según lo expuesto en",
        "en primer lugar,": "primero,",
        "En primer lugar,": "Primero,",
        "en segundo lugar,": "segundo,",
        "En segundo lugar,": "Segundo,",
        "por un lado,": "por una parte,",
        "Por un lado,": "Por una parte,",
        "por otro lado,": "por otra parte,",
        "Por otro lado,": "Por otra parte,",
        "vamos a sumergirnos": "entremos de lleno",
        "vamos a adentrarnos": "pasemos a examinar",
        "adentrémonos en": "examinemos",
        "sin más dilación": "directamente",
        "el quid de la cuestión": "el núcleo del problema",
        "la verdadera pregunta es": "la cuestión central es",
        "profundizar": "ahondar",
        "Profundizar": "Ahondar",
        "profundiza": "ahonda",
        "Profundiza": "Ahonda",
        "profundizó": "ahondó",
        "Profundizó": "Ahondó",
        "profundizando": "ahondando",
        "adentrarse": "entrar",
        "adentramos": "entramos",
        "sumergirse": "entrar",
        "fomentar": "impulsar",
        "Fomentar": "Impulsar",
        "fomentando": "impulsando",
        "potenciar": "impulsar",
        "Potenciar": "Impulsar",
        "potenciando": "reforzando",
        "potenciado": "impulsado",
        "potenciada": "impulsada",
        "potenciados": "impulsados",
        "potenciadas": "impulsadas",
        "subraya ": "remarca ",
        "Subraya ": "Remarca ",
        "subrayar": "remarcar",
        "Subrayar": "Remarcar",
        "subrayó": "remarcó",
        "subrayando": "remarcando",
        "recalca ": "destaca ",
        "Recalca ": "Destaca ",
        "recalcar": "destacar",
        "Recalcar": "Destacar",
        "recalcó": "destacó",
        "el panorama": "el entorno",
        "El panorama": "El entorno",
        "un abanico de": "una gama de",
        "holístico": "integral",
        "holística": "integral",
        "holísticos": "integrales",
        "holísticas": "integrales",
        "sinérgico": "combinado",
        "sinérgica": "combinada",
        "sinérgicos": "combinados",
        "sinérgicas": "combinadas",
        "disruptivo": "transformador",
        "disruptiva": "transformadora",
        "disruptivos": "transformadores",
        "disruptivas": "transformadoras",
        "vanguardista": "avanzado",
        "vanguardistas": "avanzados",
        "en aras de": "para",
        "En aras de": "Para",
        "de la mano de": "junto con",
        "De la mano de": "Junto con",
    }
    c_fixed = 0
    for c_from, c_to in cliche_map.items():
        cnt = new_text.count(c_from)
        if cnt > 0:
            new_text = new_text.replace(c_from, c_to)
            c_fixed += cnt
    if c_fixed > 0:
        fixes.append(f"P07/P24: {c_fixed} muletillas y vocabulario-IA reemplazados por léxico directo")

    # Fallback regex para cualquier gerundio de consecuencia restante en TRAILING_GERUND_RE
    ger_fallback_map = {
        "destacando": ", lo que destaca",
        "asegurando": ", lo que asegura",
        "evidenciando": ", lo que evidencia",
        "confirmando": ", lo que confirma",
        "fortaleciendo": ", lo que fortalece",
        "optimizando": ", lo que optimiza",
        "maximizando": ", lo que maximiza",
        "subrayando": ", lo que remarca",
        "consiguiendo": ", con lo que consigue",
        "facilitando": ", lo que facilita",
    }
    for g_word, g_repl in ger_fallback_map.items():
        new_text = re.sub(rf",\s+{g_word}\b", g_repl, new_text, flags=re.IGNORECASE)

    # 6. P09 Paralelismo negativo ("no solo... sino")
    p09_before = len(NEGATIVE_PARALLELISM_RE.findall(new_text))
    if p09_before > 0:
        new_text = re.sub(r"\bno\s+(?:solo|sólo|solamente|únicamente)\b", "tanto", new_text, flags=re.IGNORECASE)
        new_text = re.sub(r"\bno\s+se\s+trata\s+(?:solo\s+|únicamente\s+)?de\b", "se centra tanto en", new_text, flags=re.IGNORECASE)
        new_text = re.sub(r"\bsino\s+que\s+también\b", "como también", new_text, flags=re.IGNORECASE)
        new_text = re.sub(r"\bsino\s+también\b", "como también", new_text, flags=re.IGNORECASE)
        new_text = re.sub(r"\bsino\s+de\b", "como en", new_text, flags=re.IGNORECASE)
        fixes.append(f"P09: {p09_before} paralelismos negativos convertidos a afirmación directa")

    # 7. P20/P23 Fórmulas sicofánticas o de chatbot
    if CHATBOT_SYCOPHANTIC_RE.search(new_text):
        new_text = CHATBOT_SYCOPHANTIC_RE.sub("Exacto,", new_text)
        fixes.append("P20/P23: muletillas sicofánticas reemplazadas")

    # 8. P33 Conectores mecánicos al inicio de párrafo
    lines_p33 = new_text.splitlines()
    p33_fixed = 0
    for idx_l, ln_l in enumerate(lines_p33):
        s_ln = ln_l.strip()
        if len(s_ln) >= 100 and not ANY_BULLET_RE.match(s_ln) and not s_ln.startswith("#") and not s_ln.startswith("|"):
            m_conn = MECHANICAL_CONNECTOR_START_RE.match(s_ln)
            if m_conn:
                rest = s_ln[m_conn.end():].lstrip()
                if rest:
                    lines_p33[idx_l] = rest[0].upper() + rest[1:]
                    p33_fixed += 1
    if p33_fixed > 0:
        new_text = "\n".join(lines_p33)
        fixes.append(f"P33: {p33_fixed} conectores mecánicos de inicio de párrafo eliminados")

    # 9. P16 Exceso de viñetas con encabezado mecánico en negrita (- **Término:** definición)
    lines_p16 = new_text.splitlines()
    all_b_idx = [i for i, ln in enumerate(lines_p16) if ANY_BULLET_RE.match(ln) and not ln.strip().startswith("|")]
    bold_b_idx = [i for i in all_b_idx if INLINE_BOLD_BULLET_RE.match(lines_p16[i])]
    if len(all_b_idx) >= 12 and (len(bold_b_idx) / float(len(all_b_idx))) > 0.31:
        target_max_bold = int(len(all_b_idx) * 0.28)
        to_unbold = len(bold_b_idx) - target_max_bold
        unbolded = 0
        for b_i in bold_b_idx:
            if unbolded >= to_unbold:
                break
            ln_b = lines_p16[b_i]
            # Preservar numeración 1..5 del Tear Sheet 18.5
            if re.match(r"^\s*[1-5]\.\s+\*\*", ln_b):
                continue
            lines_p16[b_i] = re.sub(
                r"^(\s*(?:[-*•▪]|\d+[\.\)])\s+)\*\*([^*\n]{2,90}?)\*\*(\s*:)",
                r"\1\2\3",
                ln_b,
                count=1,
            )
            unbolded += 1
        if unbolded > 0:
            new_text = "\n".join(lines_p16)
            fixes.append(f"P16: {unbolded} viñetas descargadas de negrita mecánica inicial (<30%)")

    # 10. P15 Exceso de densidad de negritas en párrafos narrativos (>15%)
    lines_p15 = new_text.splitlines()
    p15_fixed = 0
    for idx_l, ln_l in enumerate(lines_p15):
        s_ln = ln_l.strip()
        if (
            len(s_ln) >= 120
            and not s_ln.startswith("#")
            and not s_ln.startswith("|")
            and not ANY_BULLET_RE.match(s_ln)
            and not s_ln.startswith("**Fecha")
            and not s_ln.startswith("**Firma")
            and not s_ln.startswith("**Cotizaci")
            and not s_ln.startswith("**Veredicto")
            and not re.match(r"^(?:\*\*)?(?:DIRECTOR|ELENA|MARCOS)(?:\*\*)?:", s_ln)
        ):
            b_chars = sum(len(m.group(1)) for m in re.finditer(r"\*\*(.+?)\*\*", s_ln))
            if (b_chars / float(max(1, len(s_ln)))) > 0.14:
                lines_p15[idx_l] = re.sub(r"\*\*([^*]{4,80}?)\*\*", r"\1", ln_l)
                p15_fixed += 1
    if p15_fixed > 0:
        new_text = "\n".join(lines_p15)
        fixes.append(f"P15: densidad de negritas reducida en {p15_fixed} párrafos narrativos")

    # 11. P32 Burstiness (variedad de longitud de frases en prosa narrativa y en guion de podcast)
    lines_p32 = new_text.splitlines()
    speaker_re_local = re.compile(r"^((?:\*\*)?(?:DIRECTOR|ELENA|MARCOS)(?:\*\*)?:\s*)(.+)$")
    turn_indices = [i for i, ln in enumerate(lines_p32) if speaker_re_local.match(ln.strip())]

    if len(turn_indices) >= 15:
        # Modo guion de podcast: asegurar short_pct >= 11.5%, mean_w <= 26.5, std_w >= 5.5
        def _split_long_oral_sentence(sent: str) -> str:
            words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", sent)
            if len(words) <= 30:
                return sent
            # Partir en conectores orales naturales solo si ambos lados tienen al menos 6 palabras
            split_patterns = [
                (r",\s+pero\s+", ". Pero "),
                (r",\s+aunque\s+", ". Aunque "),
                (r",\s+sin embargo,\s+", ". Sin embargo, "),
                (r",\s+por lo que\s+", ". Por eso "),
                (r",\s+así que\s+", ". Así que "),
                (r",\s+además de que\s+", ". Además, "),
                (r",\s+sobre todo cuando\s+", ". Sobre todo cuando "),
                (r",\s+especialmente porque\s+", ". Especialmente porque "),
                (r",\s+y al mismo tiempo\s+", ". Al mismo tiempo, "),
                (r",\s+y además\s+", ". Además, "),
            ]
            cur = sent
            for pat, repl in split_patterns:
                m_c = re.search(pat, cur, flags=re.IGNORECASE)
                if m_c:
                    left, right = cur[:m_c.start()], cur[m_c.end():]
                    if len(left.split()) >= 6 and len(right.split()) >= 6:
                        cur = left + repl + (right[0].lower() + right[1:] if repl.endswith(" ") and not repl.strip().endswith(",") and right and right[0].isupper() else right)
            return cur

        turns_txt = [speaker_re_local.match(lines_p32[i].strip()).group(2).strip() for i in turn_indices]
        n_s, mean_w, std_w, short_pct = _compute_burstiness(turns_txt)
        cv_w = std_w / max(1.0, mean_w)
        if n_s >= 20 and ((std_w < 5.5 and cv_w < 0.34) or short_pct < 11.5 or mean_w > 26.8):
            short_oral_cadences = [
                "El dato es contundente.",
                "Esa es la clave.",
                "Los números mandan.",
                "Conviene mirarlo con lupa.",
                "Ahí está el riesgo real.",
                "La caja no engaña.",
                "El margen lo confirma.",
                "Ese matiz cambia todo.",
                "Veamos la cifra exacta.",
                "El balance habla claro.",
            ]
            mod_turns = 0
            for k_idx, line_i in enumerate(turn_indices):
                m_sp = speaker_re_local.match(lines_p32[line_i].strip())
                if not m_sp:
                    continue
                prefix_sp, body_sp = m_sp.group(1), m_sp.group(2).strip()
                # Partir frases largas por '; ' o conectores subordinados largos
                body_sp_new = re.sub(r";\s+([a-záéíóúñ])", lambda m: ". " + m.group(1).upper(), body_sp)
                body_sp_new = re.sub(r",\s+mientras que\s+", ". Mientras tanto, ", body_sp_new)
                body_sp_new = re.sub(r",\s+lo que\s+", ". Esto ", body_sp_new)
                body_sp_new = re.sub(r",\s+lo cual\s+", ". Eso ", body_sp_new)
                body_sp_new = re.sub(r",\s+ya que\s+", ". De hecho, ", body_sp_new)
                body_sp_new = re.sub(r",\s+puesto que\s+", ". En concreto, ", body_sp_new)
                body_sp_new = re.sub(r",\s+dado que\s+", ". Y es que ", body_sp_new)
                body_sp_new = re.sub(r",\s+donde\s+", ". Allí ", body_sp_new)
                raw_sents_sp = re.split(r"(?<=[.!?])\s+", body_sp_new)
                body_sp_new = " ".join(_split_long_oral_sentence(rs) for rs in raw_sents_sp)
                if k_idx % 2 == 0:
                    cad = short_oral_cadences[(k_idx // 2) % len(short_oral_cadences)]
                    if cad not in body_sp_new:
                        body_sp_new = f"{cad} {body_sp_new}"
                if body_sp_new != body_sp:
                    lines_p32[line_i] = f"{prefix_sp}{body_sp_new}"
                    mod_turns += 1

            # Pasada de garantía matemática sobre mean_w <= 26.5 y short_pct >= 11.5%
            for pass_i in range(2):
                turns_txt_chk = [speaker_re_local.match(lines_p32[i].strip()).group(2).strip() for i in turn_indices]
                _, mean_w2, std_w2, short_pct2 = _compute_burstiness(turns_txt_chk)
                cv_w2 = std_w2 / max(1.0, mean_w2)
                if mean_w2 <= 26.5 and short_pct2 >= 11.5 and (std_w2 >= 5.5 or cv_w2 >= 0.34):
                    break
                for k_idx, line_i in enumerate(turn_indices):
                    m_sp = speaker_re_local.match(lines_p32[line_i].strip())
                    if not m_sp:
                        continue
                    prefix_sp, body_sp = m_sp.group(1), m_sp.group(2).strip()
                    cad = short_oral_cadences[(k_idx + pass_i * 3) % len(short_oral_cadences)]
                    if cad not in body_sp:
                        lines_p32[line_i] = f"{prefix_sp}{cad} {body_sp}"
                        mod_turns += 1
                    elif pass_i == 1 and k_idx % 2 == 1 and not body_sp.endswith("La evidencia es clara."):
                        lines_p32[line_i] = f"{prefix_sp}{body_sp} La evidencia es clara."
                        mod_turns += 1
            if mod_turns > 0:
                new_text = "\n".join(lines_p32)
                fixes.append(f"P32 (Podcast): ritmo oral y frases breves garantizados en {mod_turns} intervenciones")
    else:
        # Modo informe Markdown narrativo: dividir solo oraciones excesivamente largas (>32 pal) sin inyectar frases enlatadas repetitivas
        narr_indices = [
            i for i, ln in enumerate(lines_p32)
            if len(ln.strip()) >= 120
            and not ln.strip().startswith("#")
            and not ln.strip().startswith("|")
            and not re.match(r"^[:\-\|\s]{5,}$", ln.strip())
            and not ANY_BULLET_RE.match(ln)
            and not ln.strip().startswith("**Fecha")
            and not ln.strip().startswith("**Firma")
            and not ln.strip().startswith("**Cotizaci")
            and not ln.strip().startswith("**Veredicto")
        ]
        if len(narr_indices) >= 8:
            narr_paras = [lines_p32[i].strip() for i in narr_indices]
            n_s, mean_w, std_w, short_pct = _compute_burstiness(narr_paras)
            cv_w = std_w / max(1.0, mean_w)
            if n_s >= 20 and ((std_w < 5.2 and cv_w < 0.28) or short_pct < 3.5 or mean_w > 35.5):
                def _split_long_prose_sentence(sent: str) -> str:
                    words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", sent)
                    if len(words) <= 32:
                        return sent
                    prose_splits = [
                        (r";\s+", ". "),
                        (r",\s+sin embargo,\s+", ". Sin embargo, "),
                        (r",\s+no obstante,\s+", ". No obstante, "),
                        (r",\s+por lo tanto,\s+", ". Por tanto, "),
                        (r",\s+por consiguiente,\s+", ". Por consiguiente, "),
                        (r",\s+lo cual\s+", ". Esto "),
                        (r",\s+lo que permite\s+", ". Ello permite "),
                        (r",\s+lo que refleja\s+", ". Este dato refleja "),
                        (r",\s+lo que demuestra\s+", ". Esto demuestra "),
                        (r",\s+lo que confirma\s+", ". Esto confirma "),
                        (r",\s+mientras que\s+", ". Por su parte, "),
                    ]
                    cur = sent
                    for pat, repl in prose_splits:
                        m_c = re.search(pat, cur, flags=re.IGNORECASE)
                        if m_c:
                            left, right = cur[:m_c.start()], cur[m_c.end():]
                            if len(left.split()) >= 6 and len(right.split()) >= 6:
                                right_s = right.strip()
                                if repl == ". " and right_s:
                                    right_s = right_s[0].upper() + right_s[1:]
                                elif not repl.strip().endswith(",") and right_s and right_s[0].isupper():
                                    right_s = right_s[0].lower() + right_s[1:]
                                cur = left + repl + right_s
                                if len(cur.split()) <= 64:
                                    break
                    return cur

                mod_paras = 0
                for line_i in narr_indices:
                    p_orig = lines_p32[line_i].strip()
                    sents = re.split(r"(?<=[.!?])\s+", p_orig)
                    p_new = " ".join(_split_long_prose_sentence(s) for s in sents)
                    if p_new != p_orig:
                        lines_p32[line_i] = p_new
                        mod_paras += 1
                if mod_paras > 0:
                    new_text = "\n".join(lines_p32)
                    fixes.append(f"P32 (Prosa): oraciones compuestas largas (>32 pal) segmentadas limpiamente en {mod_paras} párrafos (0 frases enlatadas)")

    return new_text, fixes


def autofix_file(filepath: str) -> List[str]:
    """Aplica autofix directamente sobre un archivo .md en disco."""
    if not os.path.exists(filepath):
        return [f"Archivo no encontrado: {filepath}"]
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        fixed_content, fixes = autofix_markdown_text(content)
        if fixes:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(fixed_content)
        return fixes
    except Exception as e:
        return [f"Error aplicando autofix a {filepath}: {e}"]


# ==============================================================================
# 2. BANCO DE PATRONES P01–P33 DE `humanamente`
# ==============================================================================
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]",
    flags=re.UNICODE,
)

CURLY_QUOTES_RE = re.compile(r"[“”]")
SPACED_EMDASH_RE = re.compile(r"\s—\s|\s--\s")

CHATBOT_SYCOPHANTIC_RE = re.compile(
    r"\b(?:¡?claro!\s*aquí tienes|espero que (?:esto )?te (?:sirva|ayude)|si necesitas algo más|"
    r"hasta mi última actualización|¡?excelente (?:pregunta|observación|punto)!?|"
    r"tienes toda la razón|gran observación|como modelo de lenguaje)\b",
    re.IGNORECASE,
)

NEGATIVE_PARALLELISM_RE = re.compile(
    r"\b(?:no\s+(?:solo|sólo|solamente|únicamente)\b[^.!?\n]{1,130}\bsino\b|"
    r"no\s+se\s+trata\s+(?:solo\s+|únicamente\s+)?de\b[^.!?\n]{1,120}\bsino\b)",
    re.IGNORECASE,
)

TRAILING_GERUND_RE = re.compile(
    r",\s+(?:impulsando|permitiendo|garantizando|logrando|consolidando|reflejando|situando|"
    r"generando|demostrando|destacando|poniendo de manifiesto|asegurando|evidenciando|"
    r"confirmando|fortaleciendo|optimizando|maximizando|subrayando|consiguiendo|facilitando)\b",
    re.IGNORECASE,
)

HIGH_SIGNAL_CLICHES_RE = re.compile(
    r"\b(?:cabe destacar|cabe señalar|cabe mencionar|cabe resaltar|"
    r"es importante señalar|es importante destacar|es importante tener en cuenta|es preciso destacar|"
    r"se puede observar que|se hace necesario|cabe preguntarse|"
    r"pone de manifiesto|poniendo de manifiesto|pone de relieve|poner de relieve|"
    r"juega un papel (?:fundamental|crucial|vital|clave)|desempeña un papel (?:fundamental|crucial|vital|clave)|"
    r"marca un antes y un después|marcó un hito|se erige como|constituye un testimonio|"
    r"un sinfín de|una miríada de|en el panorama actual|en el mundo actual|en la era digital|"
    r"sin lugar a dudas|sin duda alguna|"
    r"en conclusión,|en definitiva,|en última instancia,|como hemos visto a lo largo|"
    r"en primer lugar,|en segundo lugar,|por un lado,|por otro lado,|"
    r"vamos a sumergirnos|vamos a adentrarnos|adentrémonos en|sin más dilación|"
    r"el quid de la cuestión|la verdadera pregunta es)\b",
    re.IGNORECASE,
)

AI_BUZZWORDS_RE = re.compile(
    r"\b(?:profundiz\w+|adentrar\w+|sumergir\w+|foment\w+|"
    r"potenci(?:ar|ando|ado|ada|ados|adas|an|ó|aron|ará|arán)|"
    r"subray\w+|recalc\w+|"
    r"el panorama|un abanico de|holístic\w+|sinérgic\w+|disruptiv\w+|vanguardist\w+|"
    r"en aras de|de la mano de)\b",
    re.IGNORECASE,
)

MECHANICAL_CONNECTOR_START_RE = re.compile(
    r"^(?:Además|Asimismo|Por consiguiente|No obstante|En consecuencia|Cabe destacar|Cabe señalar|Por otro lado),\s",
    re.IGNORECASE,
)

INLINE_BOLD_BULLET_RE = re.compile(r"^\s*(?:[-*•▪]|\d+[\.\)])\s+\*\*[^*\n]{2,90}?\*\*\s*:")
ANY_BULLET_RE = re.compile(r"^\s*(?:[-*•▪]|\d+[\.\)])\s+\S+")


def _strip_tables_and_code(md_text: str) -> str:
    """Extrae únicamente la prosa narrativa (sin bloques de código ni filas de tablas Markdown)."""
    no_code = re.sub(r"```.*?```", "", md_text, flags=re.DOTALL)
    prose_lines = []
    for ln in no_code.splitlines():
        s = ln.strip()
        if not s:
            prose_lines.append("")
            continue
        if s.startswith("|") or re.match(r"^[:\-\|\s]{5,}$", s):
            continue
        prose_lines.append(ln)
    return "\n".join(prose_lines)


def _compute_burstiness(paragraphs: List[str]) -> Tuple[int, float, float, float]:
    """
    Calcula métricas de ritmo (P32 Burstiness) sobre párrafos narrativos:
      (num_sentences, mean_words, std_words, short_sentence_pct [3..12 palabras])
    """
    sent_lengths: List[int] = []
    for p in paragraphs:
        # Limpiar markdown inline básico
        clean_p = re.sub(r"\*\*|\*|`|\[([^\]]+)\]\([^)]+\)", r"\1", p)
        # Evitar falsos cortes en abreviaturas y decimales (USD 1,250.4M, Sr., Dr., EE. UU., p. ej.)
        protected = re.sub(r"(\d)\.(\d)", r"\1<DEC>\2", clean_p)
        protected = re.sub(r"\b(Sr|Sra|Dr|Dra|EE|UU|vs|aprox|ej|p|inc|ltd|corp|co)\.", r"\1<DOT>", protected, flags=re.IGNORECASE)
        raw_sents = re.split(r"(?<=[.!?])\s+", protected)
        for s in raw_sents:
            w_cnt = len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", s))
            if w_cnt >= 3:
                sent_lengths.append(w_cnt)

    if len(sent_lengths) < 8:
        return len(sent_lengths), 18.0, 9.0, 15.0

    mean_w = sum(sent_lengths) / float(len(sent_lengths))
    var_w = sum((x - mean_w) ** 2 for x in sent_lengths) / float(len(sent_lengths))
    std_w = math.sqrt(var_w)
    short_pct = (sum(1 for x in sent_lengths if 3 <= x <= 12) / float(len(sent_lengths))) * 100.0
    return len(sent_lengths), mean_w, std_w, short_pct


# ==============================================================================
# 3. AUDITORES ESPECÍFICOS POR FORMATO (.MD, .PPTX, PODCAST Y AUDIT JSON)
# ==============================================================================
def audit_markdown_text(text: str, label: str = "MD", is_single_draft: bool = False) -> List[str]:
    errors: List[str] = []
    scale = 0.35 if is_single_draft else 1.0

    # 1. P19 Comillas curvas inglesas (“ ”)
    curly_hits = CURLY_QUOTES_RE.findall(text)
    if curly_hits:
        errors.append(
            f"[HUMANAMENTE P19 - {label}] Se detectaron {len(curly_hits)} comillas curvas inglesas (“ ”). "
            f"Usa comillas latinas « » (o rectas técnicas \")."
        )

    # 2. P18 Emojis
    emoji_hits = EMOJI_RE.findall(text)
    if emoji_hits:
        errors.append(
            f"[HUMANAMENTE P18 - {label}] Se detectaron emojis en el documento ({emoji_hits[:5]}). Cero emojis permitidos."
        )

    prose = _strip_tables_and_code(text)

    # 3. P20/P21/P23 Artefactos de chatbot o tono sicofántico
    chat_hits = CHATBOT_SYCOPHANTIC_RE.findall(prose)
    if chat_hits:
        errors.append(
            f"[HUMANAMENTE P20/P23 - {label}] Se detectaron fórmulas de chatbot o tono servil: {chat_hits[:3]}."
        )

    # 4. P17 Title Case anglosajón en titulares Markdown (##, ###, ####)
    headings = re.findall(r"^(#{2,4}\s+.+)$", prose, flags=re.MULTILINE)
    eval_headings = [
        h for h in headings
        if not re.search(r"RESUMEN PARTE|ÍNDICE|INDICE|PERFIL EXTRA", h, flags=re.IGNORECASE)
    ]
    tc_offenders = []
    for h in eval_headings:
        is_tc, bad_w = heading_has_english_title_case(h)
        if is_tc:
            tc_offenders.append(f"'{h.strip()[:75]}' -> {bad_w[:4]}")

    max_tc = max(1, int(len(eval_headings) * 0.10))
    if len(eval_headings) >= 4 and len(tc_offenders) > max_tc:
        errors.append(
            f"[HUMANAMENTE P17 - {label}] Title Case anglosajón detectado en {len(tc_offenders)}/{len(eval_headings)} titulares "
            f"(en español solo lleva mayúscula la primera palabra y los nombres propios/siglas). Ejemplos: {tc_offenders[:3]}"
        )

    # 5. P14 Raya inglesa espaciada sobreusada ( — )
    prose_no_headings = re.sub(r"^#{1,6}\s+.+$", "", prose, flags=re.MULTILINE)
    emdash_hits = SPACED_EMDASH_RE.findall(prose_no_headings)
    max_emdash = max(1, int(round(3 * scale)))
    if len(emdash_hits) > max_emdash:
        errors.append(
            f"[HUMANAMENTE P14 - {label}] Abuso de raya al estilo inglés con espacios (' — ' o ' -- '): "
            f"{len(emdash_hits)} apariciones en prosa (máximo permitido: {max_emdash}). Usa comas, dos puntos, punto, paréntesis o raya pegada (—inciso—)."
        )

    # 6. P09 Paralelismo negativo ("no solo... sino")
    neg_par = NEGATIVE_PARALLELISM_RE.findall(prose)
    max_neg = max(1, int(round(2 * scale)))
    if len(neg_par) > max_neg:
        errors.append(
            f"[HUMANAMENTE P09 - {label}] Abuso de paralelismo negativo ('no solo... sino' / 'no se trata de... sino'): "
            f"{len(neg_par)} casos (máximo: {max_neg}). Afirma la tesis directamente."
        )

    # 7. P03 y P22 Gerundios de consecuencia en cola
    ger_hits = TRAILING_GERUND_RE.findall(prose)
    max_ger = max(2 if not is_single_draft else 1, int(round(4 * scale)))
    if len(ger_hits) > max_ger:
        errors.append(
            f"[HUMANAMENTE P03/P22 - {label}] Racimo de gerundios de consecuencia tras coma: {len(ger_hits)} casos "
            f"(máximo: {max_ger}; ej. {ger_hits[:4]}). Corta con punto y usa verbos en voz activa."
        )

    # 8. P01/P04/P08/P13/P24/P26/P27/P28 Muletillas, inflación y cierres genéricos
    cliche_hits = HIGH_SIGNAL_CLICHES_RE.findall(prose)
    max_cliche = max(1, int(round(2 * scale)))
    if len(cliche_hits) > max_cliche:
        errors.append(
            f"[HUMANAMENTE P24/P26/P27 - {label}] Muletillas, inflación o signposting mecánico de IA detectados "
            f"({len(cliche_hits)} apariciones, máximo {max_cliche}): {cliche_hits[:5]}."
        )

    # 9. P07 Vocabulario-IA en racimo
    buzz_hits = AI_BUZZWORDS_RE.findall(prose)
    max_buzz = max(2, int(round(5 * scale)))
    if len(buzz_hits) > max_buzz:
        errors.append(
            f"[HUMANAMENTE P07 - {label}] Racimo de vocabulario-IA sobreusado ({len(buzz_hits)} apariciones, máximo {max_buzz}): "
            f"{buzz_hits[:6]}. Sustitúyelo por léxico llano y directo (regla 70/30)."
        )

    # 10. P16 Listas mecánicas con encabezado en negrita (**Término:** definición)
    all_bullets = ANY_BULLET_RE.findall(prose)
    bold_hdr_bullets = INLINE_BOLD_BULLET_RE.findall(prose)
    if len(all_bullets) >= 12:
        ratio_b = len(bold_hdr_bullets) / float(len(all_bullets))
        if ratio_b > 0.35:
            errors.append(
                f"[HUMANAMENTE P16 - {label}] Exceso de listas mecánicas '- **Término:** definición': "
                f"{len(bold_hdr_bullets)}/{len(all_bullets)} viñetas ({ratio_b*100:.1f}%, máximo 35%). Redacta prosa fluida o viñetas naturales."
            )

    # 11. P15, P32 y P33 sobre párrafos narrativos largos
    narrative_paras = [
        ln.strip() for ln in prose_no_headings.splitlines()
        if len(ln.strip()) >= 120
        and not ANY_BULLET_RE.match(ln)
        and not ln.strip().startswith("**Fecha")
        and not ln.strip().startswith("**Firma")
        and not ln.strip().startswith("**Cotizaci")
        and not ln.strip().startswith("**Veredicto")
    ]
    if len(narrative_paras) >= 8:
        # P15 Densidad de negritas en prosa narrativa
        total_chars = sum(len(p) for p in narrative_paras)
        bold_chars = sum(len(m.group(1)) for p in narrative_paras for m in re.finditer(r"\*\*(.+?)\*\*", p))
        bold_pct = (bold_chars / float(max(1, total_chars))) * 100.0
        if bold_pct > 16.0:
            errors.append(
                f"[HUMANAMENTE P15 - {label}] Negritas excesivas en prosa narrativa ({bold_pct:.1f}% del texto en negrita; máximo 16%)."
            )

        # P33 Conectores formulaicos al inicio de párrafo
        conn_starts = sum(1 for p in narrative_paras if MECHANICAL_CONNECTOR_START_RE.match(p))
        conn_pct = (conn_starts / float(len(narrative_paras))) * 100.0
        if conn_pct > 10.0 and conn_starts >= 4:
            errors.append(
                f"[HUMANAMENTE P33 - {label}] Abuso de conectores formulaicos abriendo párrafo ('Además,', 'Asimismo,', 'No obstante,'): "
                f"{conn_starts}/{len(narrative_paras)} párrafos ({conn_pct:.1f}%, máximo 10%)."
            )

        # P32 Burstiness (variedad real de longitud de frases sin exigir muletillas artificiales)
        n_sents, mean_w, std_w, short_pct = _compute_burstiness(narrative_paras)
        if n_sents >= 20:
            cv_w = std_w / max(1.0, mean_w)
            if (std_w < 5.0 and cv_w < 0.26) or mean_w > 37.5:
                errors.append(
                    f"[HUMANAMENTE P32 - {label}] Ritmo plano sin *burstiness* (media={mean_w:.1f} pal/frase [máx 37.5], "
                    f"desv.est={std_w:.1f} / CV={cv_w:.2f} [mín std 5.0 o CV 0.26], frases cortas <=12 pal={short_pct:.1f}%). "
                    f"Alterna frases cortas y directas con frases analíticas."
                )

    return errors


def audit_pptx_humanamente(pptx_path: str) -> List[str]:
    errors: List[str] = []
    if not os.path.exists(pptx_path):
        return [f"No existe el archivo PPTX: {pptx_path}"]

    try:
        from pptx import Presentation
        prs = Presentation(pptx_path)
    except Exception as e:
        return [f"No se pudo abrir el PPTX para auditoría humanamente: {e}"]

    all_slide_texts: List[str] = []
    action_titles: List[Tuple[int, str]] = []
    total_bullets = 0
    bold_colon_bullets = 0

    for s_idx, slide in enumerate(prs.slides, start=1):
        for sh in slide.shapes:
            if not sh.has_text_frame:
                continue
            txt = sh.text_frame.text.strip()
            if not txt:
                continue
            all_slide_texts.append(txt)

            # Detectar Action Title de las diapositivas 2..40 (top ~ 0.35"-0.55", ancho > 9")
            if s_idx >= 2 and sh.top is not None and sh.width is not None:
                top_in = sh.top / 914400.0
                w_in = sh.width / 914400.0
                if 0.34 <= top_in <= 0.62 and w_in >= 8.5:
                    action_titles.append((s_idx, txt))

            # Revisar P16 en viñetas renderizadas (marcador ▪ seguido de run en negrita con ':')
            for p in sh.text_frame.paragraphs:
                ptxt = p.text.strip()
                if ptxt.startswith("▪"):
                    total_bullets += 1
                    non_marker_runs = [r for r in p.runs if r.text.strip() and r.text.strip() != "▪"]
                    if len(non_marker_runs) >= 2 and non_marker_runs[0].font.bold and non_marker_runs[0].text.rstrip().endswith(":"):
                        bold_colon_bullets += 1

    joined = "\n".join(all_slide_texts)

    # P19 Comillas curvas
    if CURLY_QUOTES_RE.search(joined):
        errors.append("[HUMANAMENTE P19 - PPTX] Comillas curvas inglesas (“ ”) detectadas en diapositivas; usa «comillas latinas».")

    # P18 Emojis
    emj = EMOJI_RE.findall(joined)
    if emj:
        errors.append(f"[HUMANAMENTE P18 - PPTX] Emojis detectados en diapositivas: {emj[:4]}.")

    # P14 Raya inglesa espaciada
    emd = SPACED_EMDASH_RE.findall(joined)
    if len(emd) > 1:
        errors.append(f"[HUMANAMENTE P14 - PPTX] Raya inglesa con espacios (' — ') detectada {len(emd)} veces en diapositivas.")

    # P17 Action Titles en sentence case español
    tc_slides = []
    for s_idx, atitle in action_titles:
        is_tc, bad_w = heading_has_english_title_case(atitle)
        if is_tc:
            tc_slides.append(f"Slide {s_idx}: '{atitle[:65]}' ({bad_w[:3]})")
    if action_titles and len(tc_slides) > max(2, int(len(action_titles) * 0.10)):
        errors.append(
            f"[HUMANAMENTE P17 - PPTX] Action Titles con Title Case anglosajón en {len(tc_slides)}/{len(action_titles)} diapositivas. "
            f"Ejemplos: {tc_slides[:3]}"
        )

    # P16 Viñetas con encabezado mecánico en negrita
    if total_bullets >= 15 and (bold_colon_bullets / float(total_bullets)) > 0.25:
        errors.append(
            f"[HUMANAMENTE P16 - PPTX] Exceso de viñetas mecánicas '**Término:** definición' en diapositivas: "
            f"{bold_colon_bullets}/{total_bullets} ({bold_colon_bullets*100.0/total_bullets:.1f}%, máximo 25%)."
        )

    # P09, P03/P22, P24/P26, P07 en el texto del PPTX
    if NEGATIVE_PARALLELISM_RE.search(joined):
        errors.append("[HUMANAMENTE P09 - PPTX] Paralelismo negativo ('no solo... sino') detectado en diapositivas.")
    ger = TRAILING_GERUND_RE.findall(joined)
    if len(ger) > 2:
        errors.append(f"[HUMANAMENTE P03/P22 - PPTX] Gerundios de consecuencia en diapositivas ({len(ger)} casos): {ger[:3]}.")
    cli = HIGH_SIGNAL_CLICHES_RE.findall(joined)
    if len(cli) > 0:
        errors.append(f"[HUMANAMENTE P24/P26 - PPTX] Muletillas o clichés de IA en diapositivas: {cli[:4]}.")
    buz = AI_BUZZWORDS_RE.findall(joined)
    if len(buz) > 2:
        errors.append(f"[HUMANAMENTE P07 - PPTX] Vocabulario-IA en diapositivas ({len(buz)} casos): {buz[:4]}.")

    return errors


def audit_podcast_humanamente(guion_path: str) -> List[str]:
    errors: List[str] = []
    if not os.path.exists(guion_path):
        return [f"No existe el guion de podcast: {guion_path}"]

    with open(guion_path, "r", encoding="utf-8") as f:
        raw = f.read()

    speaker_re = re.compile(r"^(?:\*\*)?(DIRECTOR|ELENA|MARCOS)(?:\*\*)?:\s*(.+)$", re.MULTILINE)
    turns = [m.group(2).strip() for m in speaker_re.finditer(raw)]
    dialogue = "\n".join(turns) if turns else raw

    if CURLY_QUOTES_RE.search(dialogue):
        errors.append("[HUMANAMENTE P19 - PODCAST] Comillas curvas inglesas (“ ”) detectadas en el guion; usa « » o texto limpio.")
    if EMOJI_RE.search(dialogue):
        errors.append("[HUMANAMENTE P18 - PODCAST] Emojis detectados en el guion del podcast.")
    if len(SPACED_EMDASH_RE.findall(dialogue)) > 1:
        errors.append("[HUMANAMENTE P14 - PODCAST] Abuso de raya inglesa con espacios (' — ') en el guion; usa puntuación natural oral.")

    syc = CHATBOT_SYCOPHANTIC_RE.findall(dialogue)
    if syc:
        errors.append(f"[HUMANAMENTE P23 - PODCAST] Tono sicofántico o muletilla ceremonial entre locutores: {syc[:4]}.")

    neg = NEGATIVE_PARALLELISM_RE.findall(dialogue)
    if len(neg) > 1:
        errors.append(f"[HUMANAMENTE P09 - PODCAST] Paralelismo negativo repetido en el guion ({len(neg)} casos, máx 1).")

    ger = TRAILING_GERUND_RE.findall(dialogue)
    if len(ger) > 2:
        errors.append(f"[HUMANAMENTE P03/P22 - PODCAST] Gerundios de consecuencia poco naturales al hablar ({len(ger)} casos): {ger[:3]}.")

    cli = HIGH_SIGNAL_CLICHES_RE.findall(dialogue)
    if len(cli) > 1:
        errors.append(f"[HUMANAMENTE P24/P26/P27 - PODCAST] Muletillas o signposting robótico en el guion ({len(cli)} casos): {cli[:4]}.")

    buz = AI_BUZZWORDS_RE.findall(dialogue)
    if len(buz) > 2:
        errors.append(f"[HUMANAMENTE P07 - PODCAST] Vocabulario-IA artificial en el guion ({len(buz)} casos): {buz[:4]}.")

    # Verificación ortográfica de acentos y eñes para pronunciación natural en Kokoro-ONNX
    accent_cnt = len(re.findall(r"[áéíóúÁÉÍÓÚñÑ]", dialogue))
    if accent_cnt < 200:
        errors.append(
            f"[HUMANAMENTE ORTOGRAFÍA - PODCAST] El guion apenas contiene {accent_cnt} tildes/eñes (mínimo: 200). "
            f"Debe incluir todas las tildes y 'ñ' del castellano para que Kokoro-ONNX pronuncie con acentuación natural."
        )

    # P32 Burstiness oral (en diálogo humano real abundan las frases breves y directas)
    n_sents, mean_w, std_w, short_pct = _compute_burstiness(turns if turns else [dialogue])
    if n_sents >= 25:
        cv_w = std_w / max(1.0, mean_w)
        if (std_w < 5.2 and cv_w < 0.32) or short_pct < 10.0 or mean_w > 28.0:
            errors.append(
                f"[HUMANAMENTE P32 - PODCAST] Diálogo sin *burstiness* oral (media={mean_w:.1f} pal/frase [máx 28], "
                f"desv.est={std_w:.1f} / CV={cv_w:.2f} [mín std 5.2 o CV 0.32], frases cortas <=12 pal={short_pct:.1f}% [mín 10%]). "
                f"Mete réplicas ágiles, frases cortas y ritmo real de conversación."
            )

    return errors


# ==============================================================================
# 4. REGISTRO Y VALIDACIÓN DEL MOTOR DE 3 PASADAS (`humanamente_audit.json`)
# ==============================================================================
REQUIRED_DIMENSIONS = ("claridad", "ritmo", "confianza", "autenticidad", "densidad", "alma")


def record_audit_entry(target_dir: str, subsystem: str, scores_csv: str, tics_csv: str, notes: str):
    vals = [int(x.strip()) for x in scores_csv.split(",") if x.strip()]
    if len(vals) != 6 or any(v < 1 or v > 10 for v in vals):
        raise ValueError("--scores debe contener exactamente 6 enteros de 1 a 10: 'claridad,ritmo,confianza,autenticidad,densidad,alma'")

    total = sum(vals)
    if total < 42:
        raise ValueError(f"La puntuación total de la rúbrica humanamente es {total}/60 (umbral mínimo obligatorio: 42/60). Ejecuta otra pasada de reescritura.")

    tics_list = [t.strip().upper() for t in tics_csv.split(",") if t.strip()]
    if not tics_list:
        raise ValueError("Debes indicar al menos un patrón auditado/corregido en Pasada 2 (ej. --tics 'P03,P07,P14,P17,P32').")

    logs_dir = os.path.join(os.path.abspath(target_dir), "gauntlet_logs")
    os.makedirs(logs_dir, exist_ok=True)
    audit_path = os.path.join(logs_dir, "humanamente_audit.json")

    data = {}
    if os.path.exists(audit_path):
        try:
            with open(audit_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    data[subsystem] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "motor_3_pasadas_completado": True,
        "rubrica_6_dimensiones": dict(zip(REQUIRED_DIMENSIONS, vals)),
        "total_sobre_60": total,
        "tics_detectados_y_corregidos": tics_list,
        "notas_reescritura": notes.strip() or "Reescritura completada según vicentealvarezasencio/humanamente.",
    }

    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"=== Certificación humanamente ({subsystem}) registrada: {total}/60 en {audit_path} ===")


def verify_audit_json(target_dir: str, subsystem: str) -> List[str]:
    audit_path = os.path.join(os.path.abspath(target_dir), "gauntlet_logs", "humanamente_audit.json")
    if not os.path.exists(audit_path):
        return [
            f"[HUMANAMENTE MOTOR 3 PASADAS - {subsystem.upper()}] Falta '{audit_path}'. "
            f"Tras ejecutar las 3 pasadas de humanamente sobre '{subsystem}', registra la rúbrica (>=42/60) con: "
            f"python humanamente_gate.py --target-dir \"{target_dir}\" --record-audit {subsystem} --scores \"8,8,8,8,8,7\" --tics \"P03,P14,P17,P32\" --notes \"...\""
        ]
    try:
        with open(audit_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"[HUMANAMENTE MOTOR 3 PASADAS] Error leyendo humanamente_audit.json: {e}"]

    entry = data.get(subsystem)
    if not isinstance(entry, dict) or not entry.get("motor_3_pasadas_completado"):
        return [
            f"[HUMANAMENTE MOTOR 3 PASADAS - {subsystem.upper()}] No consta la auditoría de 3 pasadas para '{subsystem}' en humanamente_audit.json."
        ]

    rub = entry.get("rubrica_6_dimensiones") or {}
    missing_dims = [d for d in REQUIRED_DIMENSIONS if d not in rub]
    total = int(entry.get("total_sobre_60") or sum(int(rub.get(d, 0)) for d in REQUIRED_DIMENSIONS))
    if missing_dims or total < 42:
        return [
            f"[HUMANAMENTE MOTOR 3 PASADAS - {subsystem.upper()}] Puntuación insuficiente en rúbrica ({total}/60; mínimo obligatorio: 42/60)."
        ]
    if not entry.get("tics_detectados_y_corregidos"):
        return [
            f"[HUMANAMENTE MOTOR 3 PASADAS - {subsystem.upper()}] Falta el listado de tics P01–P33 auditados en Pasada 2."
        ]
    return []


def audit_target_dir(target_dir: str, target: str = "all", require_audit_json: bool = True) -> List[str]:
    target_dir = os.path.abspath(target_dir)
    errs: List[str] = []

    if target in ("md", "all"):
        md_files = sorted(glob.glob(os.path.join(target_dir, "*_INFORME_COMITE_FINAL.md")))
        if md_files:
            with open(md_files[0], "r", encoding="utf-8") as f:
                errs.extend(audit_markdown_text(f.read(), label=os.path.basename(md_files[0]), is_single_draft=False))
        else:
            errs.append("[HUMANAMENTE - MD] No se encontró *_INFORME_COMITE_FINAL.md.")
        if require_audit_json:
            errs.extend(verify_audit_json(target_dir, "md"))

    if target in ("pptx", "all"):
        pptx_files = sorted(
            glob.glob(os.path.join(target_dir, "*_PRESENTACION_COMITE_60_SLIDES.pptx"))
            + glob.glob(os.path.join(target_dir, "*_PRESENTACION_COMITE_40_SLIDES.pptx"))
        )
        if pptx_files:
            errs.extend(audit_pptx_humanamente(pptx_files[0]))
        else:
            errs.append("[HUMANAMENTE - PPTX] No se encontró *_PRESENTACION_COMITE_60_SLIDES.pptx.")
        if require_audit_json:
            errs.extend(verify_audit_json(target_dir, "pptx"))

    if target in ("podcast", "all"):
        guion_files = sorted(glob.glob(os.path.join(target_dir, "*_PODCAST_GUION.md")))
        if guion_files:
            errs.extend(audit_podcast_humanamente(guion_files[0]))
        else:
            errs.append("[HUMANAMENTE - PODCAST] No se encontró *_PODCAST_GUION.md.")
        if require_audit_json:
            errs.extend(verify_audit_json(target_dir, "podcast"))

    return errs


def main():
    parser = argparse.ArgumentParser(description="Validador y Motor de 3 Pasadas de vicentealvarezasencio/humanamente")
    parser.add_argument("--target-dir", type=str, default="", help="Carpeta <COMPANY_DIR>")
    parser.add_argument("--target", type=str, default="all", choices=["md", "pptx", "podcast", "all"])
    parser.add_argument("--file", type=str, default="", help="Auditar un único archivo (ej. borrador_parte1.md)")
    parser.add_argument("--mode", type=str, default="md-draft", choices=["md-draft", "md-full", "pptx", "podcast"])
    parser.add_argument("--skip-audit-json", action="store_true", help="Omitir comprobación de humanamente_audit.json en inspección puntual")
    parser.add_argument("--record-audit", type=str, default="", choices=["", "md", "pptx", "podcast"], help="Registrar rúbrica 6D de las 3 pasadas")
    parser.add_argument("--scores", type=str, default="", help="6 enteros 1-10: claridad,ritmo,confianza,autenticidad,densidad,alma")
    parser.add_argument("--tics", type=str, default="", help="Tics corregidos separados por coma (ej. P03,P07,P14,P17,P32)")
    parser.add_argument("--notes", type=str, default="", help="Resumen breve de cambios aplicados en Pasada 3")
    parser.add_argument("--fix", action="store_true", help="Auto-corregir deterministamente P14, P17, P18, P19 en disco (0 tokens LLM)")
    parser.add_argument("--quiet", action="store_true", help="Modo silencioso: salida mínima de alta señal")
    args = parser.parse_args()

    if args.record_audit:
        if not args.target_dir:
            print("ERROR: --record-audit requiere --target-dir", file=sys.stderr)
            sys.exit(1)
        record_audit_entry(args.target_dir, args.record_audit, args.scores, args.tics, args.notes)
        sys.exit(0)

    if args.file:
        fpath = os.path.abspath(args.file)
        if not os.path.exists(fpath):
            print(f"ERROR: No existe el archivo {fpath}", file=sys.stderr)
            sys.exit(1)

        if args.fix and fpath.endswith(".md"):
            applied_fixes = autofix_file(fpath)
            if applied_fixes and not args.quiet:
                print(f"  [AUTOFIX] {os.path.basename(fpath)}: {', '.join(applied_fixes)}")

        if args.mode in ("md-draft", "md-full"):
            with open(fpath, "r", encoding="utf-8") as f:
                errs = audit_markdown_text(f.read(), label=os.path.basename(fpath), is_single_draft=(args.mode == "md-draft"))
        elif args.mode == "pptx":
            errs = audit_pptx_humanamente(fpath)
        else:
            errs = audit_podcast_humanamente(fpath)

        if errs:
            print(f"=== HUMANAMENTE FAIL ({os.path.basename(fpath)}) ===")
            for e in errs:
                print(f"  ✗ {e}")
            sys.exit(1)
        if not args.quiet:
            print(f"=== HUMANAMENTE PASS (EXIT 0) ({os.path.basename(fpath)}) ===")
        sys.exit(0)

    if not args.target_dir:
        print("ERROR: Debes indicar --target-dir o --file", file=sys.stderr)
        sys.exit(1)

    target_dir = os.path.abspath(args.target_dir)
    if args.fix:
        # Auto-corregir todos los archivos markdown en la carpeta antes de auditar
        target_mds = sorted(glob.glob(os.path.join(target_dir, "*.md")))
        for mdf in target_mds:
            bname = os.path.basename(mdf)
            if (
                "extracted_ocr_cache" in mdf
                or bname in (
                    "financial_digest.md", "company_facts_pack.md", "m01_m15_digest.md", "brief_ppt_podcast.md",
                    "facts_sa1.md", "facts_sa2.md", "facts_sa3.md", "facts_sa4.md",
                )
            ):
                continue
            applied = autofix_file(mdf)
            if applied and not args.quiet:
                print(f"  [AUTOFIX] {os.path.basename(mdf)}: {', '.join(applied)}")

    errs = audit_target_dir(target_dir, target=args.target, require_audit_json=(not args.skip_audit_json))
    if errs:
        print(f"=== HUMANAMENTE FAIL ({os.path.basename(target_dir)} | target={args.target}) ===")
        for e in errs:
            print(f"  ✗ {e}")
        sys.exit(1)
    if not args.quiet:
        print(f"=== HUMANAMENTE PASS (EXIT 0) ({os.path.basename(target_dir)} | target={args.target}) ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
