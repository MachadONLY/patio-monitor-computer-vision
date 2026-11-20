"""Conferência técnica dos entregáveis Applied Computer Vision (GS 2026.2).

Valida o PDF realmente distribuído, vídeo MP4, artefatos treinados e procedência.
Não substitui reproduzir o treinamento a partir dos vídeos externos.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
CV = ROOT / "docs/gs/cv"
VISION = ROOT / "services/vision"
PDF = CV / "Patio-Monitor-Applied-Computer-Vision.pdf"
VIDEO = CV / "Patio-Monitor-Demonstracao-Visao.mp4"


def sha_file(path: Path):
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pass_if(value, description):
    if not value:
        raise AssertionError(description)
    print("PASS:", description)


def main():
    content = json.loads((CV / "relatorio-conteudo.json").read_text(encoding="utf-8"))
    report = json.loads((VISION / "artifacts/report.json").read_text(encoding="utf-8"))
    metrics = json.loads((VISION / "artifacts/metrics.json").read_text(encoding="utf-8"))
    dataset = json.loads((VISION / "dataset.json").read_text(encoding="utf-8"))

    def words(value):
        return len(re.findall(r"[\w]+(?:[–-][\w]+)*", value, flags=re.UNICODE))

    pass_if(words(content["resumo"]) == 250, "Resumo de 250 palavras no arquivo fonte")
    pass_if(words(content["objetivo"]) == 50, "Objetivo de 50 palavras no arquivo fonte")

    pdf = PdfReader(PDF)
    pass_if(len(pdf.pages) == 4, "Relatório PDF de quatro páginas")
    text = " ".join(" ".join((page.extract_text() or "").split()) for page in pdf.pages)
    for phrase in (
        "Detecção de ônibus e cruzamentos por câmera",
        "Integrantes", "Gabriel Teixeira Machado", "RM 551570",
        "Felipe Bressani", "RM 97688",
        "Camila do Prado Padalino", "RM 98316",
        "Resumo", "Introdução", "Objetivo",
        "Ferramentas e arquitetura", "Metodologia passo a passo",
        "Avaliação do detector", "Conclusão",
        "Referências e reprodução",
    ):
        pass_if(phrase in text, "PDF contém: " + phrase)
    for field in ("measured_decoder_encoder_fps", "measured_detector_fps"):
        measured = f"{report['processing'][field]:.2f}".replace(".", ",")
        pass_if(measured in text, "PDF cita velocidade medida: "+field+"="+measured)

    urls = []
    for page in pdf.pages:
        for ref in page.get("/Annots", []):
            action = ref.get_object().get("/A")
            if action and action.get("/URI"):
                urls.append(str(action["/URI"]))
    pass_if("https://github.com/MachadONLY/patio-monitor-computer-vision" in urls,
            "Link clicável do PDF aponta para a entrega pública correta")
    pass_if(not any("paidophiloo" in url for url in urls),
            "PDF não contém referência ao repositório antigo")

    passes = {
        key: value for key, value in dataset.items() if value["split"] in ("train", "validation", "test")
    }
    pass_if(len(passes) == 5, "Manifesto tem cinco vídeos originais com fontes e licenças")
    pass_if(all(row.get("sha256") and row.get("license") and row.get("download_url")
                for row in passes.values()), "Vídeos fonte possuem licença, URL e SHA-256")
    counts = Counter(v["split"] for v in passes.values())
    pass_if(counts == {"train": 3, "validation": 1, "test": 1},
            "Treino, validação e teste divididos por gravação")
    pass_if(metrics["training_frames"] == 33 and metrics["training_proposals"] == 1246,
            "Treinamento registrado em 33 quadros e 1246 propostas")
    pass_if(metrics["validation"]["frames"] == 10 and metrics["test"]["frames"] == 11,
            "Amostras de validação e teste separadas e documentadas")
    pass_if(metrics["test"]["false_positives"] == 0 and all(len(f) > 1
            for f in dataset["prague"]["frames"]),
            "Teste retido não tem quadros negativos; limitação explicitada")
    pass_if(metrics["validation"]["false_positives"] == 5,
            "Cinco previsões espúrias de validação explicitadas")
    pass_if(sha_file(VISION / "artifacts/bus-heads.npz") == metrics["checkpoint_sha256"]
            == report["model"]["sha256"], "Pesos treinados têm integridade criptográfica")
    pass_if(sha_file(VISION / "artifacts/annotated.mp4") == report["video"]["sha256"],
            "Vídeo de evidência corresponde ao relatório de inferência")
    pass_if(report["data_origin"] == "PUBLIC_VIDEO" and
            len(report["events"]) > 0 and report["events"][0]["timestamp_seconds"] == 7.44,
            "Inferência utiliza gravação pública e tem cruzamento navegável em 7,44s")

    meta = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=width,height,codec_name", "-of", "json", str(VIDEO)
    ], text=True))
    duration = float(meta["format"]["duration"])
    pass_if(duration >= 50, f"MP4 demonstrativo com duração {duration:.1f}s")
    pass_if(any(x.get("codec_name") == "h264" and x.get("width") == 1280 and
                x.get("height") == 720 for x in meta["streams"]),
            "Vídeo demonstrativo 1280×720 H.264 reproduzível")
    print("AUDITORIA DE VISÃO CONCLUÍDA: PDF, vídeo, pesos, métricas e links conferidos.")


if __name__ == "__main__":
    main()
