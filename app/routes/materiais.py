from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.forms import MaterialForm
from app.models.material import Material
from app.security import admin_required


materiais_bp = Blueprint("materiais", __name__, url_prefix="/materiais")
MATERIAIS_INDEX_ENDPOINT = "materiais.index"


@materiais_bp.get("/")
@login_required
def index():
    materiais = Material.query.order_by(Material.nome.asc()).all()
    return render_template("materiais/index.html", materiais=materiais)


@materiais_bp.route("/novo", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    form = MaterialForm()
    if form.validate_on_submit():
        material = Material(
            nome=form.nome.data.strip(),
            unidade=form.unidade.data.strip() if form.unidade.data else None,
            descricao=form.descricao.data.strip() if form.descricao.data else None,
            ativo=form.ativo.data,
        )
        db.session.add(material)
        db.session.commit()
        flash("Material cadastrado com sucesso.", "success")
        return redirect(url_for(MATERIAIS_INDEX_ENDPOINT))
    return render_template("materiais/form.html", form=form, title="Novo material")


@materiais_bp.route("/<int:material_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def edit(material_id: int):
    material = Material.query.get_or_404(material_id)
    form = MaterialForm(obj=material)
    if form.validate_on_submit():
        material.nome = form.nome.data.strip()
        material.unidade = form.unidade.data.strip() if form.unidade.data else None
        material.descricao = form.descricao.data.strip() if form.descricao.data else None
        material.ativo = form.ativo.data
        db.session.commit()
        flash("Material atualizado.", "success")
        return redirect(url_for(MATERIAIS_INDEX_ENDPOINT))
    return render_template("materiais/form.html", form=form, title="Editar material")


@materiais_bp.route("/<int:material_id>/desativar", methods=["POST"])
@login_required
@admin_required
def deactivate(material_id: int):
    material = Material.query.get_or_404(material_id)
    material.ativo = False
    db.session.commit()
    flash("Material desativado.", "info")
    return redirect(url_for(MATERIAIS_INDEX_ENDPOINT))
