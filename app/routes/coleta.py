from __future__ import annotations

from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, render_template, request

from app.extensions import db
from app.forms import ColetaEstoqueForm
from app.models.coleta_registro import ColetaRegistro
from app.models.estoque_material import EstoqueMaterial
from app.models.material import Material
from app.models.ponto_estoque import PontoEstoque
from app.services import update_stock
from app.timezone import agora_bahia
from app.utils import parse_coordinate_to_decimal, save_uploaded_image


coleta_bp = Blueprint("coleta", __name__)


@coleta_bp.route("/coleta/<token>", methods=["GET", "POST"])
def coleta_form(token: str):
    ponto = PontoEstoque.query.filter_by(coleta_token=token).first()
    if ponto is None or not ponto.ativo:
        return (
            render_template(
                "coleta/form.html",
                invalid_link=True,
                invalid_message="Link de coleta inválido ou ponto de estoque não disponível.",
            ),
            404,
        )

    form = ColetaEstoqueForm()
    estoque_items = (
        EstoqueMaterial.query.filter_by(ponto_estoque_id=ponto.id)
        .join(EstoqueMaterial.material)
        .order_by(Material.nome.asc())
        .all()
    )

    if request.method == "GET":
        return render_template(
            "coleta/form.html",
            ponto=ponto,
            form=form,
            estoque_items=estoque_items,
            confirm_mode=False,
            updates=[],
            location_registered=False,
        )

    if not form.validate_on_submit():
        return render_template(
            "coleta/form.html",
            ponto=ponto,
            form=form,
            estoque_items=estoque_items,
            confirm_mode=False,
            updates=[],
            location_registered=bool(form.latitude.data and form.longitude.data),
        )

    updates = []
    errors = []

    for item in estoque_items:
        raw_value = request.form.get(f"qtd_{item.material_id}", "").strip()
        if raw_value == "":
            nova_quantidade = Decimal(item.quantidade)
        else:
            normalized = raw_value.replace(",", ".")
            try:
                nova_quantidade = Decimal(normalized)
            except (InvalidOperation, ValueError):
                errors.append(f"Quantidade inválida para {item.material.nome}.")
                continue
        if nova_quantidade < 0:
            errors.append(f"A quantidade de {item.material.nome} não pode ser negativa.")
            continue

        atual = Decimal(item.quantidade)
        delta = nova_quantidade - atual
        updates.append(
            {
                "material": item.material,
                "anterior": atual,
                "nova": nova_quantidade,
                "delta": delta,
                "changed": delta != 0,
            }
        )

    latitude = parse_coordinate_to_decimal(form.latitude.data)
    longitude = parse_coordinate_to_decimal(form.longitude.data)
    location_registered = latitude is not None and longitude is not None

    foto_file = form.foto.data
    has_photo = bool(foto_file and hasattr(foto_file, "filename") and foto_file.filename)

    if errors:
        for message in errors:
            flash(message, "danger")
        return render_template(
            "coleta/form.html",
            ponto=ponto,
            form=form,
            estoque_items=estoque_items,
            confirm_mode=False,
            updates=updates,
            location_registered=location_registered,
        )

    is_confirm = request.form.get("confirm_update") == "1"
    foto_path = form.foto_path.data or None

    if not is_confirm:
        if has_photo:
            try:
                foto_path = save_uploaded_image(foto_file, category="coleta")
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template(
                    "coleta/form.html",
                    ponto=ponto,
                    form=form,
                    estoque_items=estoque_items,
                    confirm_mode=False,
                    updates=updates,
                    location_registered=location_registered,
                )
        return render_template(
            "coleta/form.html",
            ponto=ponto,
            form=form,
            estoque_items=estoque_items,
            confirm_mode=True,
            updates=updates,
            location_registered=location_registered,
            has_photo=bool(foto_path),
            foto_path=foto_path,
        )

    if has_photo and not foto_path:
        try:
            foto_path = save_uploaded_image(foto_file, category="coleta")
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template(
                "coleta/form.html",
                ponto=ponto,
                form=form,
                estoque_items=estoque_items,
                confirm_mode=False,
                updates=updates,
                location_registered=location_registered,
            )

    for entry in updates:
        if not entry["changed"]:
            continue
        material = entry["material"]
        anterior = entry["anterior"]
        nova = entry["nova"]
        if nova > anterior:
            update_stock(
                point=ponto,
                material=material,
                tipo="ENTRADA",
                quantidade=(nova - anterior),
                usuario=None,
                observacao=form.observacoes.data.strip() if form.observacoes.data else None,
                origem="COLETA_WEB",
            )
        elif nova < anterior:
            update_stock(
                point=ponto,
                material=material,
                tipo="SAIDA",
                quantidade=(anterior - nova),
                usuario=None,
                observacao=form.observacoes.data.strip() if form.observacoes.data else None,
                origem="COLETA_WEB",
            )

    coleta_registro = ColetaRegistro(
        ponto_estoque=ponto,
        foto=foto_path,
        latitude=latitude,
        longitude=longitude,
        observacoes=form.observacoes.data.strip() if form.observacoes.data else None,
        origem="COLETA_WEB",
    )
    db.session.add(coleta_registro)

    # Force point freshness for dashboard recency ordering.
    ponto.updated_at = agora_bahia()

    db.session.commit()
    flash("Atualização registrada com sucesso.", "success")

    estoque_items_after = (
        EstoqueMaterial.query.filter_by(ponto_estoque_id=ponto.id)
        .join(EstoqueMaterial.material)
        .order_by(Material.nome.asc())
        .all()
    )
    form = ColetaEstoqueForm()
    return render_template(
        "coleta/form.html",
        ponto=ponto,
        form=form,
        estoque_items=estoque_items_after,
        confirm_mode=False,
        updates=[],
        location_registered=False,
    )
