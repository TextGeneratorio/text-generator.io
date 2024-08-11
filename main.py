#!/usr/bin/env python
import json
import os
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlencode, quote_plus

from fastapi import Form, HTTPException
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from starlette.responses import JSONResponse, Response, RedirectResponse
from starlette.routing import Route

from questions import fixtures, doc_fixtures, tool_fixtures
from questions import blog_fixtures
from questions.db_models import User
from questions.gameon_utils import GameOnUtils
from questions.models import CreateUserRequest, GetUserRequest
from questions.payments.payments import get_self_hosted_subscription_count_for_user, get_subscription_item_id_for_user_email
from questions.utils import random_string

# pip install google-api-python-client google-cloud-storage google-auth-httplib2 google-auth-oauthlib

FACEBOOK_APP_ID = "138831849632195"
FACEBOOK_APP_SECRET = "93986c9cdd240540f70efaea56a9e3f2"

config = {}
config["webapp2_extras.sessions"] = dict(secret_key="93986c9cdd240540f70efaea56a9e3f2")

templates = Jinja2Templates(directory=".")

from fastapi import FastAPI

GCLOUD_STATIC_BUCKET_URL = "https://static.text-generator.io/static"
import sellerinfo
import stripe

from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI(
    openapi_url="/static/openapi.json",
    docs_url="/swagger-docs",
    redoc_url="/redoc",
    title="Generate Text API",
    description="Generate text, control stopping criteria like max_length/max_sentences",
    # root_path="https://api.text-generator.io",
    version="1",
)


@app.middleware("http")
async def redirect_domain(request: Request, call_next):

    # permanent redirect from language-generator.app.nz   to language-generator.io
    if request.url.hostname == "language-generator.app.nz":
        return RedirectResponse("https://text-generator.io" + request.url.path, status_code=301)
    if request.url.hostname == "language-generator.app.nz":
        return RedirectResponse("https://text-generator.io" + request.url.path, status_code=301)
    # if request.url.scheme == "http":
    #     url = request.url.with_scheme("https")
    #     return RedirectResponse(url=url)
    return await call_next(request)


app.add_middleware(GZipMiddleware, minimum_size=1000)

# app.add_middleware(HTTPSRedirectMiddleware)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/gameon/static", StaticFiles(directory="gameon/static"), name="gameon/static")

session_dict = {}

debug = (
    os.environ.get("SERVER_SOFTWARE", "").startswith("Development")
    or os.environ.get("IS_DEVELOP", "") == 1
    or Path("models/debug.env").exists()
)
if debug:
    # stripe_keys = {
    #     "secret_key": sellerinfo.STRIPE_TEST_SECRET,
    #     "publishable_key": sellerinfo.STRIPE_TEST_KEY,
    # }
    stripe_keys = {
        "secret_key": sellerinfo.STRIPE_LIVE_SECRET,
        "publishable_key": sellerinfo.STRIPE_LIVE_KEY,
    }
    GCLOUD_STATIC_BUCKET_URL = "/static"
else:
    stripe_keys = {
        "secret_key": sellerinfo.STRIPE_LIVE_SECRET,
        "publishable_key": sellerinfo.STRIPE_LIVE_KEY,
    }

stripe.api_key = stripe_keys["secret_key"]


@app.get("/")
async def index(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/index.jinja2", base_vars,
    )

@app.get("/tools")
async def tools(request: Request):
    base_vars = get_base_template_vars(request)
    tools_list = list(tool_fixtures.tools_fixtures.values())
    base_vars.update({
        "tools": tools_list,
    })
    return templates.TemplateResponse(
        "templates/tools.jinja2", base_vars,
    )

@app.get("/tools/{tool_name}")
async def tool_page(request: Request, tool_name: str):
    base_vars = get_base_template_vars(request)
    
    # Define a dictionary of available tools and their details
    tool_info = tool_fixtures.tools_fixtures.get(tool_name, {})
    
    base_vars.update({
        "tool_name": tool_info.get("name", tool_name.replace("-", " ").title()),
        "tool_description": tool_info.get("description", ""),
        "tool_keywords": tool_info.get("keywords", ""),
        "tool_url": f"/tools/{tool_name}",
        "tool_image": tool_info.get("image", ""),
        "tooltemplate": f"templates/tools/{tool_name}.jinja2"
    })

    return templates.TemplateResponse(
        "templates/tool.jinja2", base_vars,
    )
    


@app.get("/subscribe")
async def subscribe(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/subscribe.jinja2", base_vars,
    )

YOUR_DOMAIN = "https://text-generator.io"

@app.post("/create-checkout-session")
async def create_checkout_session(uid: str = Form(default=""), secret: str = Form(default=""), type: str = Form(default=""), quantity: int = Form(default=1)):
    quantity = quantity if quantity else 1
    user = session_dict.get(secret)
    stripe_id = None
    if not user or not user.stripe_id:
        user = User.byId(uid)

    if not user:
        logger.error(f"User not found: {uid}")
    else:
        stripe_id = user.stripe_id

    subscription_price = "price_0O2kLNDtz2XsjQRONTHx7Dcl"
    success_url = YOUR_DOMAIN + "/playground"
    line_item = {
        "price": subscription_price,
        'quantity': quantity,
    }

    if type and type == "annual":
        subscription_price = "price_0O2kDNDtz2XsjQRO0MCJdkeR"

        line_item = {
            "price": subscription_price,
            'quantity': quantity,
        }
    if type and type == "self-hosted":
        subscription_price = 'price_0MuAuxDtz2XsjQROz3Hp5Tcx'
        success_url = YOUR_DOMAIN + "/account"
        line_item = {
            "price": subscription_price,
            'quantity': quantity,
        }
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_id,
            # customer_email=user.email,
            line_items=[
                line_item,
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=YOUR_DOMAIN + "/",
        )
    except Exception as e:
        if "combine currencies" in str(e):
            # dropdown to old NZD plans only
            subscription_price = "price_0LCAb8Dtz2XsjQROnv1GhCL4"
            line_item = {
                "price": subscription_price,
            }
            if type and type == "self-hosted":
                subscription_price = 'price_0MuBEoDtz2XsjQROiRewGRFi'
                success_url = YOUR_DOMAIN + "/account"
                line_item = {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    "price": subscription_price,
                    'quantity': quantity,
                }
            try:
                checkout_session = stripe.checkout.Session.create(
                    customer=stripe_id,
                    line_items=[
                        line_item,
                    ],
                    mode="subscription",
                    success_url=success_url,
                    cancel_url=YOUR_DOMAIN + "/",
                )
            except Exception as ex:
                logger.error(f"Error creating checkout session: {ex}")
                return Response(str(e), status_code=500)
            return RedirectResponse(checkout_session.url, status_code=303)
        return Response(str(e), status_code=500)

    return RedirectResponse(checkout_session.url, status_code=303)


# @app.post('/webhook')
# async def webhook_received(request: Request):
#     # Replace this endpoint secret with your endpoint's unique secret
#     # If you are testing with the CLI, find the secret by running 'stripe listen'
#     # If you are using an endpoint defined with the API or dashboard, look in your webhook settings
#     # at https://dashboard.stripe.com/webhooks
#     webhook_secret = 'whsec_12345'
#     request_data = json.loads(await request.json())
#
#     if webhook_secret:
#         # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
#         signature = request.headers.get('stripe-signature')
#         try:
#             event = stripe.Webhook.construct_event(
#                 payload=await request.json(), sig_header=signature, secret=webhook_secret)
#             data = event['data']
#         except Exception as e:
#             return e
#         # Get the type of webhook event sent - used to check the status of PaymentIntents.
#         event_type = event['type']
#     else:
#         data = request_data['data']
#         event_type = request_data['type']
#     data_object = data['object']
#
#     print('event ' + event_type)
#
#     if event_type == 'checkout.session.completed':
#         print('🔔 Payment succeeded!')
#
#     elif event_type == 'customer.subscription.trial_will_end':
#         print('Subscription trial will end')
#     elif event_type == 'customer.subscription.created':
#         subscription = event['data']['object']
#     elif event_type == 'customer.subscription.updated':
#         print('Subscription created %s', event.id)
#     elif event_type == 'customer.subscription.deleted':
#         # handle subscription canceled automatically based
#         # upon your subscription settings. Or if the user cancels it.
#         print('Subscription canceled: %s', event.id)
#         subscription = event['data']['object']
#
#     return JSONResponse({'status': 'success'})


@app.get("/questions-game")
async def questions_game(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates-game/questions-game.jinja2", base_vars,

    )


@app.get("/signup")
async def signup(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/signup.jinja2", base_vars,
    )


@app.get("/where-is-ai-game")
async def signup(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/where-is-ai-game.jinja2", base_vars,

    )


@app.get("/login")
async def login(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/login.jinja2", base_vars,
    )


@app.get("/success")
async def success(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/success.jinja2", base_vars,
    )


@app.get("/logout")
async def login(request: Request):
    # clear session?
    return RedirectResponse("/", status_code=303)


@app.post("/api/create-user")
async def create_user(create_user_request: CreateUserRequest):
    email = create_user_request.email
    # emailVerified = create_user_request.emailVerified
    uid = create_user_request.uid
    photoURL = create_user_request.photoURL
    token = create_user_request.token
    # user = current_user
    # if not user:

    user = User()
    existing_user = User.byId(uid)
    if existing_user:
        user = existing_user
    # get or create
    user.id = uid
    user.email = email
    user.token = token
    user.photoURL = photoURL
    # user.emailVerified = emailVerified
    if not existing_user:  # never change secret
        user.secret = random_string(32)

    User.save(user)
    set_session_for_user(user)

    # get or create user in stripe
    if not user.stripe_id:
        customer = stripe.Customer.create(
            email=email,
            idempotency_key=uid,
        )
        user.stripe_id = customer.id
        User.save(user)
        set_session_for_user(user)

    # send_signup_email(email, referral_url_key)
    # subscription_item_id = get_subscription_item_id_for_user_email(user.email)
    # user.is_subscribed = subscription_item_id is not None
    return JSONResponse(json.loads(json.dumps(user.to_dict(), cls=GameOnUtils.MyEncoder)))


def set_session_for_user(user):
    if user != None:
        session_dict[user.secret] = user


@app.get("/portal")
async def portal_redirect(request: Request, customer_id):
    """redirect to the stripe customer portal"""
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url="https://text-generator.io/playground",
    )
    return RedirectResponse(session.url, status_code=303)


@app.post("/api/get-user")
async def get_user(get_user_request: GetUserRequest, response: Response):
    email = get_user_request.email
    user = User.byEmail(email)  # todo fix vuln
    # create the user?
    set_session_for_user(user)

    # get if the user is subscribed to a plan in stripe
    subscription_item_id = get_subscription_item_id_for_user_email(user.email)
    user.is_subscribed = subscription_item_id is not None
    num_self_hosted_instances = get_self_hosted_subscription_count_for_user(user.stripe_id)
    user.num_self_hosted_instances = int(num_self_hosted_instances) or 0

    if not user.is_subscribed:
        # recreate stripe customer if required - remediates users being created in test mode
        # stripe get customer by
        customer = stripe.Customer.retrieve(user.stripe_id)
        if not customer or not customer.id:
            customer = stripe.Customer.create(
                email=email,
                idempotency_key=email,
            )
            user.stripe_id = customer.id
            User.save(user)
            set_session_for_user(user)
    return JSONResponse(json.loads(json.dumps(user.to_dict(), cls=GameOnUtils.MyEncoder)))


def get_stripe_usage(subscription_item_id):
    """return the monthly usage of the user"""
    # get the usage for the user
    record_summary = stripe.SubscriptionItem.list_usage_record_summaries(
        subscription_item_id, limit=12
    )
    return record_summary.data


@app.post("/api/get-user/stripe-usage")
async def get_user_stripe_usage(get_user_request: GetUserRequest, response: Response):
    email = get_user_request.email
    user = User.byEmail(email)  # todo fix vuln
    # create the user?
    set_session_for_user(user)

    # get if the user is subscribed to a plan in stripe
    subscription_item_id = get_subscription_item_id_for_user_email(user.email)
    user.is_subscribed = subscription_item_id is not None
    if not user.is_subscribed:
        # recreate stripe customer if required - remediates users being created in test mode
        # stripe get customer by
        customer = stripe.Customer.retrieve(user.stripe_id)
        if not customer or not customer.id:
            customer = stripe.Customer.create(
                email=email,
                idempotency_key=email,
            )
            user.stripe_id = customer.id
            User.save(user)
            set_session_for_user(user)

    user.num_self_hosted_instances = get_self_hosted_subscription_count_for_user(user.stripe_id)

    user_to_dict = user.to_dict()
    # add info on stripe usage
    if subscription_item_id:
        user_to_dict["stripe_usage"] = get_stripe_usage(subscription_item_id) # if theres no subscription item id this will fail
    return JSONResponse(json.loads(json.dumps(user_to_dict, cls=GameOnUtils.MyEncoder)))


def track_stripe_request_usage(secret, quantity: int):
    # track a request being used in stripe
    # get the current users stripe subscription
    existing_user = session_dict.get(secret)
    if not existing_user:
        existing_user = User.bySecret(secret)
        set_session_for_user(existing_user)

    subscription_item_id = get_subscription_item_id_for_user_email(existing_user.email)
    # TODO batching
    # todo block if none
    stripe.SubscriptionItem.create_usage_record(
        subscription_item_id,
        quantity=quantity,
        # timestamp=int(time.time()),
    )


def get_base_template_vars(request: Request):
    try:
        is_mac = request.headers.get("User-Agent").lower().find("mac") != -1
    except Exception as e:
        is_mac = False

    return {
        "request": request,
        "url": request.url,
        "static_url": GCLOUD_STATIC_BUCKET_URL,
        "fixtures": json.dumps({
                                "is_mac": is_mac,
                                }),
        "stripe_publishable_key": stripe_keys["publishable_key"],
    }

@app.get("/privacy")
async def privacy(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/privacy.jinja2", base_vars,
    )


@app.get("/account")
async def account(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/account.jinja2", base_vars,
    )


@app.get("/terms")
async def terms(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/terms.jinja2", base_vars,
    )


@app.get("/contact")
async def contact(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/contact.jinja2", base_vars,
    )


@app.get("/about")
async def about(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/about.jinja2", base_vars,
    )

@app.get("/self-hosting")
async def selfhosting(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/selfhosting.jinja2", base_vars,
    )

@app.get("/success")
async def success(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/success.jinja2", base_vars,
    )


@app.get("/how-it-works")
async def howitworks(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/howitworks.jinja2", base_vars,
    )


@app.get("/playground")
async def playground(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/playground.jinja2", base_vars,
    )


@app.get("/sitemap")
async def sitemap(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/sitemap.jinja2", base_vars,
    )


@app.get("/docs")
async def docs(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/docs.jinja2", base_vars,
    )

@app.get("/text-to-speech")
async def text_to_speech(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/text-to-speech.jinja2", base_vars,
    )

@app.get("/use-cases/{usecase}")
async def use_case_route(request: Request, usecase: str):
    use_case = deepcopy(fixtures.use_cases.get(usecase))
    url_key = urlencode(use_case["generate_params"], quote_via=quote_plus)
    input_text = use_case["generate_params"]["text"]

    results = use_case["results"]
    for result in results:
        result["generated_text"] = result["generated_text"][len(input_text) :]
    base_vars = get_base_template_vars(request)
    base_vars.update({
            "description": use_case["description"],
            "title": use_case["title"],
            "results": results,
            "text": input_text,
            "use_case": use_case,
            "url_key": url_key,
        })
    return templates.TemplateResponse(
        "templates/use-case.jinja2", base_vars,
    )


@app.get("/use-cases")
async def use_cases(request: Request):
    use_cases = deepcopy(fixtures.use_cases).items()

    base_vars = get_base_template_vars(request)
    base_vars.update({
            "use_cases": use_cases,
        })
    return templates.TemplateResponse(
        "templates/use-cases.jinja2", base_vars,
    )


@app.get("/blog/{name}")
async def blog_name(request: Request, name: str):
    blog = deepcopy(blog_fixtures.blogs.get(name))
    base_vars = get_base_template_vars(request)
    base_vars.update({
            "blog": blog,
            "description": blog["description"],
            "title": blog["title"],
            "keywords": blog["keywords"],
            "blogtemplate": "/templates/shared/" + name + ".jinja2",
        })
    return templates.TemplateResponse(
        "templates/blog.jinja2", base_vars,
    )


@app.get("/blog")
async def blog(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
            "blogs": blog_fixtures.blogs.items(),
        })
    return templates.TemplateResponse(
        "templates/blogs.jinja2", base_vars,
    )


@app.get("/docs/{name}")
async def doc_name(request: Request, name: str):
    doc = deepcopy(doc_fixtures.docs.get(name))
    base_vars = get_base_template_vars(request)
    base_vars.update({
            "doc": doc,
            "description": doc["description"],
            "title": doc["title"],
            "keywords": doc["keywords"],
            "blogtemplate": "/templates/shared/" + name + ".jinja2",
        })
    return templates.TemplateResponse(
        "templates/doc.jinja2", base_vars,
    )

@app.get("/bulk-text-generator")
async def bulk_text_generator(request: Request):
    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/bulk.jinja2", base_vars,
    )


@app.get("/sitemap.xml")
async def sitemap_xml(request: Request, response: Response):
    response.headers["Content-Type"] = "text/xml; charset=utf-8"

    base_vars = get_base_template_vars(request)
    base_vars.update({
    })
    return templates.TemplateResponse(
        "templates/sitemap.xml.jinja2", base_vars,
    )


# All the routes are stored in app.routes
for route in app.routes:
    # Check if route is an instance of the class Route and not of any other class like BaseRoute
    # AND check if the name of the route is openapi
    if route.__class__ == Route and route.name == "openapi":
        # Remove the route from the list
        app.router.routes.remove(route)


@app.get("/openapi.json")
async def openapi(request: Request):
    # render json file openapi.json
    # read dict
    with open("static/openapi.json") as f:
        text = f.read()
        j = json.loads(text)
        # set api key in example

        return JSONResponse(j)

@app.get("/file{file_path:path}")
async def file(file_path: str, request: Request):
    # redirect to "api." and gradio_tts
    current_url = request.url
    if "localhost" in current_url.hostname or "127." in current_url.hostname:
        return RedirectResponse(url="http://localhost:8000/gradio_tts/file" + str(file_path))
    return RedirectResponse(url="https://api.text-generator.io/gradio_tts/file" + str(file_path))


def validate_generate_params(generate_params):
    validate_result = ""
    if generate_params.text == "":
        validate_result = "Please enter some text"
    return validate_result


## serve favicon.ico from root
app.mount("/", StaticFiles(directory="static"), name="favicon")
