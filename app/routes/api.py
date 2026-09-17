from __future__ import annotations

from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.extensions import db
from app.models.estoque_material import EstoqueMaterial
from app.models.material import Material
from app.models.municipio import Municipio
from app.models.ponto_estoque import PontoEstoque
from app.models.territorio import Territorio
from app.services import build_map_points, get_dashboard_metrics


api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/territorios")
@login_required
def list_territorios():
    territorios = Territorio.query.filter_by(ativo=True).order_by(Territorio.nome.asc()).all()
    return jsonify(
        [
            {"id": territorio.id, "nome": territorio.nome, "codigo": territorio.codigo, "ativo": territorio.ativo}
            for territorio in territorios
        ]
    )


@api_bp.get("/municipios")
@login_required
def list_municipios():
    municipios = Municipio.query.filter_by(ativo=True).order_by(Municipio.nome.asc()).all()
    return jsonify(
        [
            {
                "id": municipio.id,
                "nome": municipio.nome,
                "territorio_id": municipio.territorio_id,
                "territorio_nome": municipio.territorio.nome,
                "latitude": float(municipio.latitude) if municipio.latitude is not None else None,
                "longitude": float(municipio.longitude) if municipio.longitude is not None else None,
            }
            for municipio in municipios
        ]
    )


@api_bp.get("/materiais")
@login_required
def list_materiais():
    materiais = Material.query.filter_by(ativo=True).order_by(Material.nome.asc()).all()
    return jsonify(
        [
            {"id": material.id, "nome": material.nome, "unidade": material.unidade, "descricao": material.descricao}
            for material in materiais
        ]
    )


@api_bp.get("/estoques")
@login_required
def list_estoques():
    pontos = PontoEstoque.query.order_by(PontoEstoque.nome.asc()).all()
    return jsonify(
        [
            {
                "id": ponto.id,
                "nome": ponto.nome,
                "municipio": ponto.municipio.nome,
                "territorio": ponto.municipio.territorio.nome,
                "ativo": ponto.ativo,
            }
            for ponto in pontos
        ]
    )


@api_bp.get("/estoques/<int:ponto_id>")
@login_required
def get_estoque(ponto_id: int):
    ponto = PontoEstoque.query.get_or_404(ponto_id)
    estoque = EstoqueMaterial.query.filter_by(ponto_estoque_id=ponto.id).join(EstoqueMaterial.material).order_by(Material.nome.asc()).all()
    return jsonify(
        {
            "id": ponto.id,
            "nome": ponto.nome,
            "municipio": ponto.municipio.nome,
            "territorio": ponto.municipio.territorio.nome,
            "endereco": ponto.endereco,
            "latitude": float(ponto.latitude) if ponto.latitude is not None else None,
            "longitude": float(ponto.longitude) if ponto.longitude is not None else None,
            "responsavel_nome": ponto.responsavel_nome,
            "responsavel_telefone": ponto.responsavel_telefone,
            "responsavel_whatsapp": ponto.responsavel_whatsapp,
            "foto": ponto.foto,
            "estoque": [
                {"material": item.material.nome, "quantidade": float(item.quantidade)} for item in estoque
            ],
        }
    )


@api_bp.post("/estoques")
@login_required
def create_estoque():
    data = request.get_json(silent=True) or {}
    required = ["nome", "municipio_id"]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing)}"}), 400

    municipio = Municipio.query.get_or_404(int(data["municipio_id"]))
    ponto = PontoEstoque(
        nome=data["nome"],
        municipio=municipio,
        endereco=data.get("endereco"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        responsavel_nome=data.get("responsavel_nome"),
        responsavel_telefone=data.get("responsavel_telefone"),
        responsavel_whatsapp=data.get("responsavel_whatsapp"),
        foto=data.get("foto"),
        observacoes=data.get("observacoes"),
        ativo=bool(data.get("ativo", True)),
    )
    db.session.add(ponto)
    db.session.commit()
    return jsonify({"id": ponto.id, "message": "Ponto criado com sucesso."}), 201


@api_bp.put("/estoques/<int:ponto_id>")
@login_required
def update_estoque(ponto_id: int):
    ponto = PontoEstoque.query.get_or_404(ponto_id)
    data = request.get_json(silent=True) or {}
    if "nome" in data:
        ponto.nome = data["nome"]
    if "municipio_id" in data:
        ponto.municipio = Municipio.query.get_or_404(int(data["municipio_id"]))
    if "endereco" in data:
        ponto.endereco = data["endereco"]
    if "latitude" in data:
        ponto.latitude = data["latitude"]
    if "longitude" in data:
        ponto.longitude = data["longitude"]
    if "responsavel_nome" in data:
        ponto.responsavel_nome = data["responsavel_nome"]
    if "responsavel_telefone" in data:
        ponto.responsavel_telefone = data["responsavel_telefone"]
    if "responsavel_whatsapp" in data:
        ponto.responsavel_whatsapp = data["responsavel_whatsapp"]
    if "foto" in data:
        ponto.foto = data["foto"]
    if "observacoes" in data:
        ponto.observacoes = data["observacoes"]
    if "ativo" in data:
        ponto.ativo = bool(data["ativo"])
    db.session.commit()
    return jsonify({"id": ponto.id, "message": "Ponto atualizado com sucesso."})


@api_bp.get("/dashboard")
@login_required
def dashboard_data():
    filters = {
        key: request.args.get(key, type=int)
        for key in ("territorio_id", "municipio_id", "material_id")
        if request.args.get(key)
    }
    filters["status"] = request.args.get("status")
    metrics = get_dashboard_metrics(filters)
    return jsonify(
        {
            "total_points": metrics["total_points"],
            "total_municipios": metrics["total_municipios"],
            "total_territorios": metrics["total_territorios"],
            "total_materiais": metrics["total_materiais"],
            "total_banners": float(metrics["total_banners"]),
        }
    )


@api_bp.get("/mapa")
@login_required
def mapa_data():
    filters = {
        key: request.args.get(key, type=int)
        for key in ("territorio_id", "municipio_id", "material_id")
        if request.args.get(key)
    }
    filters["status"] = request.args.get("status")
    return jsonify(build_map_points(filters))
