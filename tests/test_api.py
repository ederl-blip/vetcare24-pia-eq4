"""Pruebas de la API: códigos 200/201/400/404/409/422 y mensajes claros."""

import pytest


def test_health_y_catalogo(client):
    assert client.get("/health").json() == {"estado": "ok"}
    cat = client.get("/catalogo").json()
    assert len(cat) == 20 and cat[0]["precio_mxn"] == "313.00"


def test_200_consultar_y_listar(client):
    r = client.get("/operaciones/VET-O001")
    assert r.status_code == 200 and r.json()["total_mxn"] == "7587.00"
    lista = client.get("/operaciones", params={"limite": 5, "estado": "SOLICITADA"})
    assert lista.status_code == 200 and len(lista.json()) == 5


def test_404_cita_inexistente(client):
    r = client.get("/operaciones/NOPE")
    assert r.status_code == 404 and "No existe la cita" in r.json()["detail"]
    assert client.post("/operaciones/NOPE/confirmar").status_code == 404


def test_201_crear_cita(client):
    r = client.post("/operaciones", json={
        "actor_id": "VET-C001", "lineas": [{"recurso_id": "VET-P001", "cantidad": 2}]})
    assert r.status_code == 201
    assert r.json()["estado"] == "SOLICITADA" and r.json()["total_mxn"] == "626.00"


@pytest.mark.parametrize("cuerpo", [
    {"actor_id": "VET-C001", "lineas": []},
    {"actor_id": "VET-C001", "lineas": [{"recurso_id": "VET-P001", "cantidad": 0}]},
    {"lineas": [{"recurso_id": "VET-P001", "cantidad": 1}]},
])
def test_422_datos_mal_formados(client, cuerpo):
    assert client.post("/operaciones", json=cuerpo).status_code == 422


def test_404_crear_con_tutor_o_servicio_inexistente(client):
    r = client.post("/operaciones", json={"actor_id": "NOPE", "lineas": [{"recurso_id": "VET-P001", "cantidad": 1}]})
    assert r.status_code == 404
    r = client.post("/operaciones", json={"actor_id": "VET-C001", "lineas": [{"recurso_id": "NOPE", "cantidad": 1}]})
    assert r.status_code == 404


def test_flujo_confirmar_realizar_con_eventos(client):
    assert client.post("/operaciones/VET-O001/confirmar").json()["estado"] == "CONFIRMADA"
    assert client.post("/operaciones/VET-O001/realizar").json()["estado"] == "REALIZADA"
    nombres = [e["nombre"] for e in client.get("/operaciones/VET-O001/eventos").json()]
    assert nombres == ["OperacionConfirmada", "OperacionRealizada"]


def test_409_transicion_invalida_con_mensaje_claro(client):
    client.post("/operaciones/VET-O001/confirmar")
    r = client.post("/operaciones/VET-O001/confirmar")
    assert r.status_code == 409
    assert r.json()["detail"] == "No se puede confirmar una cita que está en estado CONFIRMADA"
    r = client.post("/operaciones/VET-O002/realizar")
    assert r.status_code == 409 and "SOLICITADA" in r.json()["detail"]


def test_409_sin_lugares_y_400_no_procesable(client):
    op = client.post("/operaciones", json={
        "actor_id": "VET-C001", "lineas": [{"recurso_id": "VET-P001", "cantidad": 99}]}).json()
    r = client.post(f"/operaciones/{op['id']}/confirmar")
    assert r.status_code == 409 and "lugares suficientes" in r.json()["detail"]
    sin_auth = client.post("/operaciones", json={
        "actor_id": "VET-C001", "autorizado": False,
        "lineas": [{"recurso_id": "VET-P001", "cantidad": 1}]}).json()
    r = client.post(f"/operaciones/{sin_auth['id']}/confirmar")
    assert r.status_code == 400 and "autorización" in r.json()["detail"]


def test_cancelar_y_evaluacion(client):
    assert client.post("/operaciones/VET-O003/cancelar").json()["estado"] == "CANCELADA"
    ev = client.get("/operaciones/VET-O001/evaluacion").json()
    assert set(ev) >= {"total_mxn", "puede_procesarse", "aplica_beneficio"}


def test_listar_estado_invalido_es_422(client):
    assert client.get("/operaciones", params={"estado": "XYZ"}).status_code == 422


def test_us13_tutor_duplicado_409_y_201(client):
    cuerpo = {"nombre": "Ana Torres", "telefono": "81 1234 5678", "correo": "ana@correo.com"}
    assert client.post("/tutores", json=cuerpo).status_code == 201
    r = client.post("/tutores", json={"nombre": "Ana T.", "telefono": "(81) 1234-5678"})
    assert r.status_code == 409 and "Ya existe un expediente activo" in r.json()["detail"]
    r = client.post("/tutores", json={**cuerpo, "nombre": "Luis", "confirmar_distinta_persona": True})
    assert r.status_code == 201
    assert client.post("/tutores", json={"nombre": "Sin contacto"}).status_code == 400


def test_us11_alergia_bloquea_con_409_y_permite_confirmar(client):
    masc = client.post("/mascotas", json={"nombre": "Luna", "propietario_id": "VET-C001",
                                          "alergias": ["penicilina"]})
    assert masc.status_code == 201
    mid = masc.json()["id"]
    receta = {"medicamento": "Penicilina G", "sustancias": ["penicilina"]}
    r = client.post(f"/mascotas/{mid}/recetas", json=receta)
    assert r.status_code == 409 and "alérgica a penicilina" in r.json()["detail"]
    r = client.post(f"/mascotas/{mid}/recetas", json={
        **receta, "confirmar_conscientemente": True, "veterinario": "Dra. Ruiz"})
    assert r.status_code == 201 and r.json()["con_alerta"] is True
    assert client.post("/mascotas/999/recetas", json=receta).status_code == 404
    ok = client.post(f"/mascotas/{mid}/recetas", json={"medicamento": "Meloxicam", "sustancias": ["meloxicam"]})
    assert ok.status_code == 201 and ok.json()["con_alerta"] is False


def test_us06_urgencia(client):
    base = {"ahora": "2026-11-06T10:10:00", "hora_cierre": "2026-11-06T20:00:00",
            "citas": [{"id": 1, "mascota_id": 1, "inicio": "2026-11-06T10:00:00", "fin": "2026-11-06T10:30:00"},
                      {"id": 2, "mascota_id": 2, "inicio": "2026-11-06T10:30:00", "fin": "2026-11-06T11:00:00"}]}
    r = client.post("/agenda/urgencias", json={**base, "mascota_id": 5, "motivo": "Atropello"})
    assert r.status_code == 200
    assert r.json()["citas"][0]["estado"] == "PAUSADA" and r.json()["citas"][1]["inicio"] == "2026-11-06T10:50:00"
    r = client.post("/agenda/urgencias", json={**base, "motivo": "Atropello"})
    assert r.status_code == 400 and "identificador de la mascota" in r.json()["detail"]
    tarde = {**base, "hora_cierre": "2026-11-06T11:10:00", "mascota_id": 5, "motivo": "x"}
    assert client.post("/agenda/urgencias", json=tarde).status_code == 409
