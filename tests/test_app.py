def post(client, url, **data):
    # Login/logout reset the session (a security feature), so use the current CSRF token.
    with client.session_transaction() as sess:
        token = sess.setdefault("csrf_token", "tok")
    return client.post(url, data={"csrf_token": token, **data}, follow_redirects=True)


def register(client, name="prnce", password="password123"):
    return post(client, "/register", username=name, password=password)


def test_login_required(client):
    response = client.get("/")
    assert response.status_code == 302 and "/login" in response.headers["Location"]


def test_csrf_blocks_post_without_token(client):
    response = client.post("/register", data={"username": "prnce", "password": "password123"})
    assert response.status_code == 400


def test_register_add_and_auto_categorize(client):
    assert b"Add transaction" in register(client).data
    html = post(client, "/transactions", kind="expense", amount="25", description="jeep fare").data
    assert b"Transaction added." in html
    assert b"Transportation" in html


def test_users_cannot_see_each_others_data(client):
    register(client, "alice")
    post(client, "/transactions", kind="expense", amount="99", description="secret purchase")
    post(client, "/logout")
    html = register(client, "bobby").data
    assert b"secret purchase" not in html


def test_xss_is_escaped(client):
    register(client)
    html = post(client, "/transactions", kind="expense", amount="5", description="<script>alert(1)</script>").data
    assert b"<script>alert(1)</script>" not in html
    assert b"&lt;script&gt;" in html


def test_invalid_input_shows_error(client):
    register(client)
    html = post(client, "/transactions", kind="expense", amount="-5", description="bad").data
    assert b"greater than zero" in html


def test_wrong_password_rejected(client):
    register(client, "prnce", "password123")
    post(client, "/logout")
    html = post(client, "/login", username="prnce", password="nope-nope-nope").data
    assert b"Invalid username or password." in html
