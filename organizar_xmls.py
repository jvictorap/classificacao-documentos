from pathlib import Path
import datetime
import re

def apagar_arquivos_xml(caminho_pasta: Path):
    pasta = Path(caminho_pasta)
    for arquivo in pasta.iterdir():
        if arquivo.suffix.lower() == ".xml":
            try:
                print('-' * 100)
                print(f'Apagando arquivo: {arquivo.name}')
                arquivo.unlink()
            except Exception as e:
                print(f'Erro ao apagar o arquivo {arquivo.name}: {e}')
                continue

def norm_digits(s):
    """Retorna só os dígitos da string (ou '' se None)."""
    if not s:
        return ""
    return "".join(ch for ch in str(s) if ch.isdigit())

def sanitize_name(name, max_len=120):
    """Remove caracteres inválidos e compacta espaços; retorna uppercase."""
    if not name:
        return "DESCONHECIDO"
    s = str(name).strip()
    s = re.sub(r'[\\/:*?"<>|]', "", s)     # remove inválidos
    s = re.sub(r"\s+", " ", s)             # compacta espaços
    return s[:max_len].strip().upper()

def is_gado_by_ncms(ncms):
    """
    Regra tolerante para GADO:
    - qualquer NCM que comece por '0102' é considerado GADO (cobre 01022190, 01022919, etc.)
    """
    for n in ncms:
        nn = norm_digits(n)
        if not nn:
            continue
        if nn.startswith("0102"):
            return True
    return False

def is_leite_by_ncms(ncms):
    """Regra para LEITE: NCM exatamente 04012090 ou que zfilled seja igual (tolerância)."""
    for n in ncms:
        nn = norm_digits(n)
        if not nn:
            continue
        if nn == "04012090" or nn.zfill(8) == "04012090"  or nn == "04014010" or nn.zfill(8) == "04014010":
            return True
    return False

def apagar_arquivos_pdf(caminho_pasta: Path):
    for arquivo in caminho_pasta.iterdir():
        if arquivo.suffix.lower() == ".pdf":
            try:
                print('-' * 100)
                print(f'Apagando arquivo: {arquivo.name}')
                arquivo.unlink()
            except Exception as e:
                print(f'Erro ao apagar o arquivo {arquivo.name}: {e}')
                continue


# importa NfeProc
try:
    from nfelib.nfe.bindings.v4_0.proc_nfe_v4_00 import NfeProc
except Exception as ee:
    raise RuntimeError("Não consegui importar NfeProc. Verifique se 'nfelib' está instalada no env. Erro: " + str(ee))



while True:
    # -------------------------
    # Configurações
    # -------------------------
    BASE = Path(input("Caminho da pasta base: ").strip())
    RECEITAS = BASE / "RECEITAS"
    GADO_FOLDER = RECEITAS / "GADO"
    LEITE_FOLDER = RECEITAS / "LEITE"
    DANFES_FOLDER = RECEITAS / "DANFES"

    # -------------------------
    # Funções utilitárias
    # -------------------------


    # -------------------------
    # Execução
    # -------------------------
    # encontra XMLs (case-insensitive)
    xmls = list(BASE.rglob("*.xml")) + list(BASE.rglob("*.XML"))
    # dedup
    _seen = set()
    xml_files = []
    for p in xmls:
        kp = str(p.resolve())
        if kp not in _seen:
            _seen.add(kp)
            xml_files.append(p)

    print(f"[{datetime.datetime.now().isoformat()}] Pasta base: {BASE}")
    print(f"[{datetime.datetime.now().isoformat()}] XMLs encontrados: {len(xml_files)}")

    # cria pastas de saída
    for d in (DANFES_FOLDER, GADO_FOLDER, LEITE_FOLDER):
        d.mkdir(parents=True, exist_ok=True)

    processed = saved = errors = 0

    for i, xml_path in enumerate(xml_files, start=1):
        processed += 1
        print("\n" + "="*40)
        print(f"[{i}/{len(xml_files)}] Processando: {xml_path}")

        # tenta carregar NfeProc
        try:
            nfe = NfeProc.from_path(xml_path)
        except Exception as e:
            print(f" ERRO: falha ao carregar XML: {e}")
            errors += 1
            continue

        # tenta gerar PDF (to_pdf ou fallbacks)
        pdf_bytes = None
        try:
            if hasattr(nfe, "to_pdf"):
                pdf_bytes = nfe.to_pdf()
            else:
                # fallback genérico
                for alt in ("render_pdf", "export_pdf", "toPDF"):
                    fn = getattr(nfe, alt, None)
                    if callable(fn):
                        try:
                            pdf_bytes = fn()
                            break
                        except Exception:
                            pdf_bytes = None
            if not pdf_bytes:
                raise RuntimeError("Geração de PDF retornou vazio/None.")
        except Exception as e:
            print(f" ERRO: não foi possível gerar PDF: {e}")
            errors += 1
            continue

        # extrai número/emitente/destinatário
        try:
            numero = str(getattr(nfe.NFe.infNFe.ide, "nNF", "SEM_NUMERO")).strip()
        except Exception:
            numero = "SEM_NUMERO"
        try:
            emitente_raw = getattr(nfe.NFe.infNFe.emit, "xNome", None) or getattr(nfe.NFe.infNFe.emit, "XNome", None) or "FORNECEDOR_DESCONHECIDO"
            emitente = sanitize_name(emitente_raw)
        except Exception:
            emitente = "FORNECEDOR_DESCONHECIDO"
        try:
            destinatario_raw = getattr(nfe.NFe.infNFe.dest, "xNome", None) or getattr(nfe.NFe.infNFe.dest, "XNome", None) or "DESTINATARIO_DESCONHECIDO"
            destinatario = sanitize_name(destinatario_raw)
        except Exception:
            destinatario = "DESTINATARIO_DESCONHECIDO"

        # coleta NCMs (tolerante a variações)
        ncms = []
        try:
            dets = list(nfe.NFe.infNFe.det)
            for det in dets:
                ncm_val = None
                try:
                    ncm_val = getattr(det.prod, "NCM", None)
                except Exception:
                    ncm_val = None
                if not ncm_val:
                    ncm_val = getattr(det.prod, "ncm", None) or getattr(det.prod, "Ncm", None)
                if ncm_val:
                    ncms.append(str(ncm_val))
        except Exception:
            pass

        ncms_norm = [norm_digits(x) for x in ncms if x]
        print(" NCMs detectados (bruto):", ncms)
        print(" NCMs normalizados: ", ncms_norm)

        # Decide destino
        destino_dir = DANFES_FOLDER
        if is_gado_by_ncms(ncms):
            # cria pasta do fornecedor dentro de GADO (sanitizado) e salva lá
            fornecedor_folder = GADO_FOLDER / emitente
            fornecedor_folder.mkdir(parents=True, exist_ok=True)
            destino_dir = fornecedor_folder
            print(" Rota: GADO -> pasta do fornecedor:", fornecedor_folder)
        elif is_leite_by_ncms(ncms):
            destino_dir = LEITE_FOLDER
            print(" Rota: LEITE")
        else:
            DANFES_FOLDER.mkdir(exist_ok=True)
            destino_dir = DANFES_FOLDER
            print(" Rota: PADRÃO (DANFES)")

        # monta nome do arquivo
        nome = f"N° {numero} - {destinatario} X {emitente}.pdf"
        nome = "".join(c for c in nome if c not in r'\/:*?"<>|')
        out_path = destino_dir / nome

        # evita sobrescrever
        counter = 1
        base_stem = out_path.stem
        base_suf = out_path.suffix or ".pdf"
        while out_path.exists():
            counter += 1
            out_path = destino_dir / f"{base_stem}_{counter}{base_suf}"

        # grava arquivo
        try:
            out_path.write_bytes(pdf_bytes)
            saved += 1
            print(f" OK: salvo em -> {out_path}")
        except Exception as e:
            errors += 1
            print(f" ERRO: ao salvar arquivo: {e}")

    apagar_arquivos_xml(BASE)
    apagar_arquivos_pdf(BASE)
    # resumo
    print("\n" + "="*40)
    print(f"Processados: {processed} | Salvos: {saved} | Erros: {errors}")
    print(f"Pasta RECEITAS usada: {RECEITAS}")
    print("="*40 + "\n")
