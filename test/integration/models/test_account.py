from linode_api4.objects.account import Account

@pytest.fixture(scope="session", autouse=True)
def test_create_account(get_client):
    client = get_client
    account = Account(client=client, id="test")
    account.make(id="test1", client=client, cls="account")

    print(account)

# def test_account_view():
# def test_notifications_list():
# def test_oauth_clients_list():
# def test_oauth_clinet_create():
# def test_oauth_client_view():
# def test_oauth_client_update():
# def test_oauth_client_secret_reset():
# def test_oauth_client_thumbnail_view():
# def test_oauth_client_thumbnail_update():
# def test_payment_methods_list():
# def test_payment_method_add():
# def test_payment_method_view():
# def test_payment_method_make_default():
# def test_payments_list():
# def test_payment_make():
# def test_paypal_payment_stage():
# def test_staged_approved_paypal_payment_execute():
# def test_payment_view():
# def test_promo_credit_add():
# def test_service_transfers_list():
# def test_service_transfer_create():
# def test_service_transfer_view():
# def test_service_transfer_accept():
# def test_account_settings_view():
# def test_account_settings_update_():
# def test_service_transfer_create():
# def test_linode_managed_eneabled():
# def test_network_utilization_view():
# def test_users_list():
# def test_user_create():
# def test_user_view():
# def test_user_update():
# def test_user_grants_view():
# def test_user_grants_update():
