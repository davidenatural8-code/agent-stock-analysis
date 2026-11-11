import os
import glob

root = r'C:\Users\david\Desktop\Momentum\FLASH_TO_PROCESS\REMAINING'
dirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith('_')]

status = {}
for d in dirs:
    p = os.path.join(root, d)
    has_f0 = os.path.exists(os.path.join(p, 'facts_sa1.md'))
    bp1 = os.path.exists(os.path.join(p, 'borrador_parte1.md'))
    bp2 = os.path.exists(os.path.join(p, 'borrador_parte2.md'))
    bp3 = os.path.exists(os.path.join(p, 'borrador_parte3.md'))
    bp4 = os.path.exists(os.path.join(p, 'borrador_parte4.md'))
    bp5 = os.path.exists(os.path.join(p, 'borrador_parte5.md'))
    digest = os.path.exists(os.path.join(p, 'm01_m15_digest.md'))
    master = len(glob.glob(os.path.join(p, '*_INFORME_COMITE_FINAL.md'))) > 0
    docx = len(glob.glob(os.path.join(p, '*_INFORME_INSTITUCIONAL_FINAL.docx'))) > 0
    pptx = len(glob.glob(os.path.join(p, '*_PRESENTACION_COMITE_60_SLIDES.pptx'))) > 0
    guion_files = glob.glob(os.path.join(p, '*_PODCAST_GUION.md'))
    guion = len(guion_files) > 0
    
    guion_pass = False
    guion_words = 0
    guion_turns = 0
    if guion:
        gfile = guion_files[0]
        size = os.path.getsize(gfile)
        with open(gfile, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        guion_words = len(content.split())
        has_speakers = all(sp in content for sp in ['DIRECTOR:', 'ELENA:', 'MARCOS:'])
        guion_turns = content.count('DIRECTOR:') + content.count('ELENA:') + content.count('MARCOS:')
        if guion_words >= 8000 and guion_turns >= 85 and has_speakers:
            guion_pass = True

    status[d] = {
        'drafts': sum([bp1, bp2, bp3, bp4]),
        'digest': digest,
        'bp5': bp5,
        'master': master,
        'derivatives': (docx and pptx),
        'guion': guion,
        'guion_pass': guion_pass,
        'guion_words': guion_words,
        'guion_turns': guion_turns,
        'missing_drafts': [i+1 for i, exists in enumerate([bp1, bp2, bp3, bp4]) if not exists]
    }

total = len(dirs)
guion_ready = sum(1 for d, s in status.items() if s['guion_pass'])
derivatives_ready = sum(1 for d, s in status.items() if s['derivatives'] and not s['guion_pass'])
master_ready = sum(1 for d, s in status.items() if s['master'] and not s['derivatives'])
bp5_ready = sum(1 for d, s in status.items() if s['bp5'] and not s['master'])
digest_ready = sum(1 for d, s in status.items() if s['digest'] and not s['bp5'])
drafts_4 = sum(1 for d, s in status.items() if s['drafts'] == 4 and not s['digest'])
drafts_partial = sum(1 for d, s in status.items() if 0 < s['drafts'] < 4)
no_drafts = sum(1 for d, s in status.items() if s['drafts'] == 0)

print(f"Total folders: {total}")
print(f"Guion certified PASS (EXIT 0 ready): {guion_ready}")
print(f"Derivatives ready (need podcast): {derivatives_ready}")
print(f"Master ready (need derivatives): {master_ready}")
print(f"BP5 ready (need master): {bp5_ready}")
print(f"Digest ready (need BP5): {digest_ready}")
print(f"Drafts 1-4 ready (need digest): {drafts_4}")
print(f"Drafts partial: {drafts_partial}")
print(f"No drafts started: {no_drafts}")

print("\nNon-completed detailed:")
for d, s in sorted(status.items()):
    if not s['guion_pass']:
        print(f"{d:12}: drafts={s['drafts']}/4 (missing={s['missing_drafts']}) digest={s['digest']} bp5={s['bp5']} master={s['master']} deriv={s['derivatives']} guion={s['guion']} (words={s['guion_words']}, turns={s['guion_turns']})")
