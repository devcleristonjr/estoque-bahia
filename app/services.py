from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func

from app.extensions import db
from app.models.estoque_material import EstoqueMaterial
from app.models.material import Material
from app.models.movimentacao_estoque import MovimentacaoEstoque
from app.models.municipio import Municipio
from app.models.ponto_estoque import PontoEstoque
from app.models.territorio import Territorio
from app.utils import build_whatsapp_url


def _apply_point_filters(query, filters: dict):
    if territorio_id := filters.get("territorio_id"):
        query = query.filter(Municipio.territorio_id == territorio_id)
    if municipio_id := filters.get("municipio_id"):
        query = query.filter(PontoEstoque.municipio_id == municipio_id)
    if status := filters.get("status"):
        if status == "ativo":
            query = query.filter(PontoEstoque.ativo.is_(True))
        elif status == "inativo":
            query = query.filter(PontoEstoque.ativo.is_(False))
    return query.distinct()


def _banner_filter(query, filters: dict):
    query = query.join(EstoqueMaterial.material)
    if material_id := filters.get("material_id"):
        return query.filter(EstoqueMaterial.material_id == material_id)
    return query.filter(Material.nome.ilike("%banner%"))


def _aggregate_banner_total(filters: dict) -> Decimal:
    query = (
        db.session.query(func.coalesce(func.sum(EstoqueMaterial.quantidade), 0))
        .select_from(PontoEstoque)
        .join(PontoEstoque.municipio)
        .join(PontoEstoque.estoques)
        .join(EstoqueMaterial.material)
    )
    query = _apply_point_filters(query, filters)
    if material_id := filters.get("material_id"):
        query = query.filter(EstoqueMaterial.material_id == material_id)
    query = _banner_filter(query, filters)
    value = query.scalar() or Decimal("0")
    return Decimal(value)


def get_dashboard_metrics(filters: dict | None = None) -> dict:
    filters = filters or {}
    base_points = PontoEstoque.query.join(PontoEstoque.municipio)
    base_points = _apply_point_filters(base_points, filters)
    if material_id := filters.get("material_id"):
        base_points = base_points.join(PontoEstoque.estoques).filter(EstoqueMaterial.material_id == material_id)
    active_points = base_points.filter(PontoEstoque.ativo.is_(True))

    total_points = active_points.count()
    point_totals_subquery = active_points.with_entities(
        PontoEstoque.id.label("ponto_id"),
        PontoEstoque.municipio_id.label("municipio_id"),
        Municipio.territorio_id.label("territorio_id"),
    ).subquery()
    total_municipios = db.session.query(func.count(func.distinct(point_totals_subquery.c.municipio_id))).scalar() or 0
    total_territorios = db.session.query(func.count(func.distinct(point_totals_subquery.c.territorio_id))).scalar() or 0
    total_materiais = (
        db.session.query(func.count(func.distinct(EstoqueMaterial.material_id)))
        .select_from(EstoqueMaterial)
        .join(EstoqueMaterial.ponto_estoque)
        .join(PontoEstoque.municipio)
    )
    if material_id := filters.get("material_id"):
        total_materiais = total_materiais.filter(EstoqueMaterial.material_id == material_id)
    total_materiais = _apply_point_filters(total_materiais, filters).scalar() or 0

    total_banners = _aggregate_banner_total(filters)
    recent_points = active_points.order_by(PontoEstoque.updated_at.desc()).limit(5).all()
    top_banner_points = (
        db.session.query(
            PontoEstoque,
            func.coalesce(func.sum(EstoqueMaterial.quantidade), 0).label("banner_total"),
        )
        .join(PontoEstoque.municipio)
        .join(PontoEstoque.estoques)
    )
    top_banner_points = _apply_point_filters(top_banner_points.filter(PontoEstoque.ativo.is_(True)), filters)
    if material_id := filters.get("material_id"):
        top_banner_points = top_banner_points.filter(EstoqueMaterial.material_id == material_id)
    top_banner_points = _banner_filter(top_banner_points, filters)
    top_banner_points = (
        top_banner_points.group_by(PontoEstoque.id)
        .order_by(func.coalesce(func.sum(EstoqueMaterial.quantidade), 0).desc())
        .limit(5)
        .all()
    )
    recent_movements = (
        db.session.query(MovimentacaoEstoque)
        .join(MovimentacaoEstoque.ponto_estoque)
        .filter(PontoEstoque.ativo.is_(True))
        .order_by(MovimentacaoEstoque.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_points": total_points,
        "total_municipios": total_municipios,
        "total_territorios": total_territorios,
        "total_materiais": total_materiais,
        "total_banners": total_banners,
        "recent_points": recent_points,
        "top_banner_points": top_banner_points,
        "recent_movements": recent_movements,
    }


def build_map_points(filters: dict | None = None) -> list[dict]:
    filters = filters or {}
    query = (
        db.session.query(PontoEstoque)
        .join(PontoEstoque.municipio)
        .join(Municipio.territorio)
        .filter(PontoEstoque.latitude.isnot(None), PontoEstoque.longitude.isnot(None))
    )
    query = _apply_point_filters(query, filters)
    if material_id := filters.get("material_id"):
        query = query.join(PontoEstoque.estoques).filter(EstoqueMaterial.material_id == material_id)

    points = []
    for point in query.order_by(PontoEstoque.nome.asc()).all():
        if filters.get("material_id"):
            banner_total = (
                db.session.query(func.coalesce(func.sum(EstoqueMaterial.quantidade), 0))
                .select_from(EstoqueMaterial)
                .filter(
                    EstoqueMaterial.ponto_estoque_id == point.id,
                    EstoqueMaterial.material_id == filters["material_id"],
                )
                .scalar()
                or Decimal("0")
            )
        else:
            banner_total = (
                db.session.query(func.coalesce(func.sum(EstoqueMaterial.quantidade), 0))
                .select_from(EstoqueMaterial)
                .join(EstoqueMaterial.material)
                .filter(EstoqueMaterial.ponto_estoque_id == point.id, Material.nome.ilike("%banner%"))
                .scalar()
                or Decimal("0")
            )
        points.append(
            {
                "id": point.id,
                "nome": point.nome,
                "municipio": point.municipio.nome,
                "territorio": point.municipio.territorio.nome,
                "latitude": float(point.latitude),
                "longitude": float(point.longitude),
                "responsavel_nome": point.responsavel_nome,
                "responsavel_whatsapp": point.responsavel_whatsapp,
                "whatsapp_url": build_whatsapp_url(point.responsavel_whatsapp or point.responsavel_telefone),
                "foto": point.foto,
                "total_banners": float(banner_total),
                "detail_url": f"/estoques/{point.id}",
            }
        )
    return points


def update_stock(point: PontoEstoque, material: Material, tipo: str, quantidade: Decimal, usuario, observacao: str | None = None) -> MovimentacaoEstoque:
    stock = EstoqueMaterial.query.filter_by(ponto_estoque_id=point.id, material_id=material.id).first()
    if stock is None:
        stock = EstoqueMaterial(ponto_estoque=point, material=material, quantidade=Decimal("0"))
        db.session.add(stock)
        db.session.flush()

    quantidade_anterior = Decimal(stock.quantidade or 0)
    if tipo == "ENTRADA":
        quantidade_posterior = quantidade_anterior + quantidade
        movimento_quantidade = quantidade
    elif tipo == "SAIDA":
        quantidade_posterior = quantidade_anterior - quantidade
        movimento_quantidade = quantidade
        if quantidade_posterior < 0:
            raise ValueError("A saída não pode deixar o estoque negativo.")
    else:
        quantidade_posterior = quantidade
        movimento_quantidade = abs(quantidade_posterior - quantidade_anterior)

    stock.quantidade = quantidade_posterior
    movimento = MovimentacaoEstoque(
        ponto_estoque=point,
        material=material,
        tipo=tipo,
        quantidade=movimento_quantidade,
        quantidade_anterior=quantidade_anterior,
        quantidade_posterior=quantidade_posterior,
        observacao=observacao,
        usuario=usuario,
    )
    db.session.add(movimento)
    db.session.flush()
    return movimento
