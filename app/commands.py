from __future__ import annotations

import click
from flask import current_app

from app.extensions import db
from app.models.usuario import Usuario


def register_commands(app):
    @app.cli.command("create-admin")
    @click.option("--nome", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--senha", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(nome: str, email: str, senha: str) -> None:
        existing = Usuario.query.filter_by(email=email.lower()).first()
        if existing:
            click.echo("Já existe um usuário com este e-mail.")
            return

        usuario = Usuario(nome=nome, email=email.lower(), perfil="ADMIN", ativo=True)
        usuario.set_password(senha)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuário administrador criado: {usuario.email}")
