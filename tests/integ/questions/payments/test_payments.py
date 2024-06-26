from questions.payments.payments import get_subscription_item_id_for_user, \
    get_self_hosted_subscription_item_id_for_user, get_self_hosted_subscription_count_for_user, \
    create_subscription_for_user


def test_get_sub():
    customer = 'cus_NGdulPTZbDAHyS'
    # subscription = get_subscription_item_id_for_user(customer)
    # assert subscription == None
    #
    subscription = get_self_hosted_subscription_item_id_for_user(customer)
    assert subscription != None
    #
    #
    subscription_count = get_self_hosted_subscription_count_for_user(customer)
    assert subscription_count == 1
    customer = "cus_NIJwYWFTeOmhaG" # fraud payment
    subscription_count = get_self_hosted_subscription_count_for_user(customer)
    assert subscription_count == 0


def test_get_sub_nic():
    customer = "cus_NHhzgHTQr8pQIv"
    subscription = get_subscription_item_id_for_user(customer)
    assert subscription != None
    print(subscription)


def test_get_sub_nic2():
    customer = "cus_LvDjjvSIblFAn9"
    subscription = get_subscription_item_id_for_user(customer)
    assert subscription != None
    print(subscription)

def test_create_subscription():
    customer  = "cus_NJRDGwDIP6ced1"
    subscription = create_subscription_for_user(customer)

    assert subscription != None
    print(subscription)
