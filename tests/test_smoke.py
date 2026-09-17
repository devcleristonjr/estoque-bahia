from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models.municipio import Municipio
from app.models.ponto_estoque import PontoEstoque
from app.models.territorio import Territorio
from app.models.usuario import Usuario
from app.utils import parse_coordinate_pair
from config import TestingConfig


def test_login_and_dashboard_smoke():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        user = Usuario(nome="Admin", email="admin@example.com", perfil="ADMIN", ativo=True)
        user.set_password("123456")
        db.session.add(user)
        db.session.commit()

    client = app.test_client()
    response = client.get("/", follow_redirects=False)
    assert response.status_code in {302, 401}

    login_response = client.post(
        "/login",
        data={"email": "admin@example.com", "password": "123456"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200
    assert b"Dashboard" in login_response.data


def test_admin_routes_for_user_and_geographic_management():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        admin = Usuario(nome="Admin", email="admin@example.com", perfil="ADMIN", ativo=True)
        admin.set_password("123456")
        db.session.add(admin)
        territorio = Territorio(nome="Extremo Sul", codigo="ES", ativo=True)
        db.session.add(territorio)
        db.session.flush()
        municipio = Municipio(nome="Ilhéus", territorio_id=territorio.id, codigo_ibge="2903208", ativo=True)
        db.session.add(municipio)
        db.session.commit()

    client = app.test_client()
    client.post(
        "/login",
        data={"email": "admin@example.com", "password": "123456"},
        follow_redirects=True,
    )

    usuarios_response = client.get("/usuarios/")
    assert usuarios_response.status_code == 200
    assert "Usuários" in usuarios_response.get_data(as_text=True)

    territorios_response = client.get("/territorios/")
    assert territorios_response.status_code == 200
    assert "Territórios" in territorios_response.get_data(as_text=True)

    municipios_response = client.get("/municipios/")
    assert municipios_response.status_code == 200
    assert "Municípios" in municipios_response.get_data(as_text=True)


def test_parse_coordinate_pair_accepts_google_maps_dms():
    latitude, longitude = parse_coordinate_pair("12°55'39.9\"S 38°23'14.8\"W")
    assert latitude == Decimal("-12.92775")
    assert longitude == Decimal("-38.38744444444444444444444444")


def test_parse_coordinate_pair_accepts_google_maps_dms_with_comma_separator():
    latitude, longitude = parse_coordinate_pair("12°55'39.9\"S, 38°23'14.8\"W")
    assert latitude == Decimal("-12.92775")
    assert longitude == Decimal("-38.38744444444444444444444444")


def test_point_created_with_google_maps_coordinates_appears_on_map():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        admin = Usuario(nome="Admin", email="admin@example.com", perfil="ADMIN", ativo=True)
        admin.set_password("123456")
        db.session.add(admin)
        territorio = Territorio(nome="Extremo Sul", codigo="ES", ativo=True)
        db.session.add(territorio)
        db.session.flush()
        municipio = Municipio(nome="Itabuna", territorio_id=territorio.id, codigo_ibge="2903208", ativo=True)
        db.session.add(municipio)
        db.session.commit()

    client = app.test_client()
    client.post(
        "/login",
        data={"email": "admin@example.com", "password": "123456"},
        follow_redirects=True,
    )

    response = client.post(
        "/estoques/novo",
        data={
            "nome": "Ponto teste",
            "municipio_id": "1",
            "coordenadas": "12°55'39.9\"S 38°23'14.8\"W",
            "endereco": "Rua X",
            "ativo": "y",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        api_response = client.get("/api/mapa")
        payload = api_response.get_json()
        assert isinstance(payload, list)
        assert any(item["nome"] == "Ponto teste" for item in payload)


def test_multiple_points_are_returned_by_map_api():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        admin = Usuario(nome="Admin", email="admin@example.com", perfil="ADMIN", ativo=True)
        admin.set_password("123456")
        db.session.add(admin)
        territorio = Territorio(nome="Extremo Sul", codigo="ES", ativo=True)
        db.session.add(territorio)
        db.session.flush()
        municipio = Municipio(nome="Itabuna", territorio_id=territorio.id, codigo_ibge="2903208", ativo=True)
        municipio_2 = Municipio(nome="Ilhéus", territorio_id=territorio.id, codigo_ibge="2913606", ativo=True)
        db.session.add_all([municipio, municipio_2])
        db.session.commit()
        db.session.add_all(
            [
                PontoEstoque(
                    nome="Ponto A",
                    municipio_id=municipio.id,
                    latitude=Decimal("-12.92775"),
                    longitude=Decimal("-38.387444"),
                    ativo=True,
                ),
                PontoEstoque(
                    nome="Ponto B",
                    municipio_id=municipio_2.id,
                    latitude=Decimal("-14.793968"),
                    longitude=Decimal("-39.039157"),
                    ativo=True,
                ),
            ]
        )
        db.session.commit()

    client = app.test_client()
    client.post(
        "/login",
        data={"email": "admin@example.com", "password": "123456"},
        follow_redirects=True,
    )

    response = client.get("/api/mapa")
    payload = response.get_json()
    assert response.status_code == 200
    assert isinstance(payload, list)
    assert {item["nome"] for item in payload} >= {"Ponto A", "Ponto B"}


def test_edit_stock_point_without_new_photo_does_not_crash():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        admin = Usuario(nome="Admin", email="admin@example.com", perfil="ADMIN", ativo=True)
        admin.set_password("123456")
        db.session.add(admin)
        territorio = Territorio(nome="Extremo Sul", codigo="ES", ativo=True)
        db.session.add(territorio)
        db.session.flush()
        municipio = Municipio(nome="Itabuna", territorio_id=territorio.id, codigo_ibge="2903208", ativo=True)
        db.session.add(municipio)
        db.session.flush()
        ponto = PontoEstoque(
            nome="Ponto original",
            municipio_id=municipio.id,
            endereco="Rua antiga",
            latitude=Decimal("-12.92775"),
            longitude=Decimal("-38.387444"),
            ativo=True,
        )
        db.session.add(ponto)
        db.session.commit()
        ponto_id = ponto.id
        municipio_id = municipio.id

    client = app.test_client()
    client.post(
        "/login",
        data={"email": "admin@example.com", "password": "123456"},
        follow_redirects=True,
    )

    response = client.post(
        f"/estoques/{ponto_id}/editar",
        data={
            "nome": "Ponto atualizado",
            "municipio_id": str(municipio_id),
            "coordenadas": "12°55'39.9\"S 38°23'14.8\"W",
            "endereco": "Rua nova",
            "ativo": "y",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
