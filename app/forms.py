from __future__ import annotations

from decimal import Decimal

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import BooleanField, DecimalField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class UsuarioForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(max=120)])
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=180)])
    perfil = SelectField(
        "Perfil",
        choices=[("ADMIN", "Administrador"), ("OPERADOR", "Operador"), ("VISUALIZADOR", "Visualizador")],
        validators=[DataRequired()],
    )
    ativo = BooleanField("Ativo", default=True)
    senha = PasswordField("Senha", validators=[Optional(), Length(min=6, max=255)])


class TerritorioForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(max=180)])
    codigo = StringField("Código", validators=[Optional(), Length(max=50)])
    ativo = BooleanField("Ativo", default=True)


class MunicipioForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(max=180)])
    territorio_id = SelectField("Território", coerce=int, validators=[DataRequired()])
    codigo_ibge = StringField("Código IBGE", validators=[Optional(), Length(max=20)])
    latitude = StringField("Latitude", validators=[Optional()])
    longitude = StringField("Longitude", validators=[Optional()])
    ativo = BooleanField("Ativo", default=True)


class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), Email(), Length(max=180)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=6, max=255)])
    remember_me = BooleanField("Lembrar-me")


class MaterialForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(max=180)])
    unidade = StringField("Unidade", validators=[Optional(), Length(max=40)])
    descricao = TextAreaField("Descrição", validators=[Optional(), Length(max=2000)])
    ativo = BooleanField("Ativo", default=True)


class PontoEstoqueForm(FlaskForm):
    nome = StringField("Nome do local", validators=[DataRequired(), Length(max=180)])
    municipio_id = SelectField("Município", coerce=int, validators=[DataRequired()])
    endereco = StringField("Endereço", validators=[Optional(), Length(max=255)])
    coordenadas = StringField("Coordenadas do Google Maps", validators=[Optional()])
    latitude = StringField("Latitude", validators=[Optional()])
    longitude = StringField("Longitude", validators=[Optional()])
    responsavel_nome = StringField("Nome do responsável", validators=[Optional(), Length(max=180)])
    responsavel_telefone = StringField("Telefone", validators=[Optional(), Length(max=30)])
    responsavel_whatsapp = StringField("WhatsApp", validators=[Optional(), Length(max=30)])
    foto = FileField("Foto do local")
    observacoes = TextAreaField("Observações", validators=[Optional(), Length(max=4000)])
    ativo = BooleanField("Ativo", default=True)


class EstoqueMovimentacaoForm(FlaskForm):
    material_id = SelectField("Material", coerce=int, validators=[DataRequired()])
    tipo = SelectField(
        "Tipo",
        choices=[("ENTRADA", "Entrada"), ("SAIDA", "Saída"), ("AJUSTE", "Ajuste")],
        validators=[DataRequired()],
    )
    quantidade = DecimalField(
        "Quantidade",
        places=2,
        rounding=None,
        validators=[DataRequired(), NumberRange(min=Decimal("0.01"))],
    )
    observacao = TextAreaField("Observação", validators=[Optional(), Length(max=4000)])
